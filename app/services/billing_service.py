from datetime import datetime
from decimal import Decimal
from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.function.automatic_bill_id_generation import generate_bill_id
from app.models.bill import Bill, BillType, PaymentStatus
from app.models.customer import Customer
from app.models.inventory import InventoryTransaction
from app.models.item import Item
from app.models.supplier import Supplier
from app.models.user import User
from app.services.alert_service import AlertService
from app.services.customer_service import CustomerService
from app.services.financial_service import FinancialService, ZERO
from app.services.payment_service import PaymentService
from app.services.supplier_service import SupplierService


class BillingService:
    @staticmethod
    def _get_item_for_update(db: Session, model_number: str) -> Item:
        item = db.query(Item).filter(Item.model_number == model_number).with_for_update().first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with model number {model_number} not found",
            )
        return item

    @staticmethod
    def _resolve_parties(
        *,
        db: Session,
        bill_type: str,
        customer_id: int | None,
        supplier_id: int | None,
    ) -> tuple[Customer | None, Supplier | None]:
        customer: Customer | None = None
        if customer_id is not None:
            if bill_type != BillType.sell.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="customer_id can only be used with sell bills",
                )
            customer = CustomerService.ensure_active_customer(CustomerService.get_customer(db, customer_id))

        supplier: Supplier | None = None
        if supplier_id is not None:
            if bill_type != BillType.buy.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="supplier_id can only be used with buy bills",
                )
            supplier = SupplierService.ensure_active_supplier(SupplierService.get_supplier(db, supplier_id))

        return customer, supplier

    @staticmethod
    def create_bill(
        *,
        db: Session,
        user: User,
        bill_type: str,
        items: Iterable,
        customer_id: int | None = None,
        supplier_id: int | None = None,
        discount_amount: Decimal = ZERO,
        tax_amount: Decimal = ZERO,
        initial_paid_amount: Decimal = ZERO,
        payment_method: str | None = None,
        payment_mode_summary: str | None = None,
        notes: str | None = None,
        finalized_at: datetime | None = None,
    ) -> Bill:
        if bill_type not in {BillType.buy.value, BillType.sell.value}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="bill_type must be either 'buy' or 'sell'",
            )

        items = list(items)
        if not items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one bill item is required",
            )

        customer, supplier = BillingService._resolve_parties(
            db=db,
            bill_type=bill_type,
            customer_id=customer_id,
            supplier_id=supplier_id,
        )

        bill = Bill(
            bill_code=generate_bill_id(bill_type),
            bill_type=BillType(bill_type),
            customer_id=customer.id if customer else None,
            supplier_id=supplier.id if supplier else None,
            discount_amount=FinancialService.money(discount_amount),
            tax_amount=FinancialService.money(tax_amount),
            paid_amount=ZERO,
            payment_status=PaymentStatus.unpaid,
            payment_mode_summary=payment_mode_summary or payment_method,
            notes=notes,
            finalized_at=finalized_at or datetime.utcnow(),
            created_by=user.id,
        )
        db.add(bill)
        db.flush()

        subtotal_amount = ZERO
        for line in items:
            item = BillingService._get_item_for_update(db, line.model_number)

            if line.quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Quantity must be greater than 0 for {line.model_number}",
                )

            if bill.bill_type == BillType.sell:
                if item.quantity < line.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Not enough stock for {item.model_number}",
                    )
                item.quantity -= line.quantity
                price = FinancialService.money(item.selling_price)
            else:
                item.quantity += line.quantity
                price = FinancialService.money(item.buying_price)

            line_total = FinancialService.money(price * line.quantity)
            subtotal_amount = FinancialService.money(subtotal_amount + line_total)

            db.add(
                InventoryTransaction(
                    bill_id=bill.id,
                    item_id=item.id,
                    quantity=line.quantity,
                    price=price,
                    transaction_type=bill.bill_type.value,
                )
            )

            if item.quantity < user.alert_threshold:
                AlertService.upsert_low_stock_alert(
                    db=db,
                    item_id=item.id,
                    user_id=user.id,
                    current_quantity=item.quantity,
                )
            else:
                AlertService.resolve_alert(db=db, item_id=item.id, user_id=user.id)

        bill.subtotal_amount = FinancialService.money(subtotal_amount)
        bill.total_amount = FinancialService.calculate_total(
            subtotal_amount=bill.subtotal_amount,
            discount_amount=bill.discount_amount,
            tax_amount=bill.tax_amount,
        )
        FinancialService.validate_paid_amount(total_amount=bill.total_amount, paid_amount=initial_paid_amount)
        bill.paid_amount = FinancialService.money(initial_paid_amount)
        FinancialService.refresh_bill_financials(bill)

        if FinancialService.money(initial_paid_amount) > ZERO:
            PaymentService.create_initial_payment(
                db=db,
                bill=bill,
                amount=initial_paid_amount,
                payment_method=payment_method,
                notes=notes,
                created_by=user.id,
                paid_at=bill.finalized_at,
            )

        if bill.customer_id:
            FinancialService.recalculate_customer_due_balance(db, bill.customer_id)
        if bill.supplier_id:
            FinancialService.recalculate_supplier_payable_balance(db, bill.supplier_id)

        db.commit()
        bill = (
            db.query(Bill)
            .options(
                joinedload(Bill.customer),
                joinedload(Bill.supplier),
                joinedload(Bill.inventory_transactions).joinedload(InventoryTransaction.items),
                joinedload(Bill.payments),
            )
            .filter(Bill.id == bill.id)
            .first()
        )
        return bill

    @staticmethod
    def get_bill(db: Session, bill_id: int) -> Bill:
        bill = (
            db.query(Bill)
            .options(
                joinedload(Bill.customer),
                joinedload(Bill.supplier),
                joinedload(Bill.inventory_transactions).joinedload(InventoryTransaction.items),
                joinedload(Bill.payments),
            )
            .filter(Bill.id == bill_id)
            .first()
        )
        if not bill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bill with id {bill_id} not found")
        return bill

    @staticmethod
    def list_bills(db: Session) -> list[Bill]:
        return (
            db.query(Bill)
            .options(joinedload(Bill.customer), joinedload(Bill.supplier))
            .order_by(Bill.created_at.desc(), Bill.id.desc())
            .all()
        )

    @staticmethod
    def list_due_bills(db: Session) -> list[Bill]:
        return (
            db.query(Bill)
            .options(joinedload(Bill.customer))
            .filter(
                Bill.bill_type == BillType.sell,
                Bill.finalized_at.isnot(None),
                Bill.payment_status != PaymentStatus.paid,
            )
            .order_by(Bill.created_at.desc(), Bill.id.desc())
            .all()
        )

    @staticmethod
    def list_payable_bills(db: Session) -> list[Bill]:
        return (
            db.query(Bill)
            .options(joinedload(Bill.supplier))
            .filter(
                Bill.bill_type == BillType.buy,
                Bill.finalized_at.isnot(None),
                Bill.payment_status != PaymentStatus.paid,
            )
            .order_by(Bill.created_at.desc(), Bill.id.desc())
            .all()
        )
