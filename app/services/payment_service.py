from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.models.bill import Bill, BillType, PaymentStatus
from app.models.customer import Customer
from app.models.payment import Payment, PaymentDirection, PaymentMethod, PaymentType
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.payment import (
    CustomerDuePaymentCreate,
    CustomerDueSummaryResponse,
    DashboardPartyBalance,
    DueDashboardSummaryResponse,
    LedgerEntryResponse,
    PaymentCreate,
    PaymentCreateResult,
    SupplierLedgerResponse,
    SupplierPayablePaymentCreate,
    SupplierPayableSummaryResponse,
    CustomerLedgerResponse,
)
from app.services.customer_service import CustomerService
from app.services.financial_service import FinancialService, ZERO
from app.services.supplier_service import SupplierService


class PaymentService:
    @staticmethod
    def _payment_method(value: str | None) -> PaymentMethod:
        if not value:
            return PaymentMethod.cash
        try:
            return PaymentMethod(value)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment_method") from exc

    @staticmethod
    def _payment_created_at(payload: PaymentCreate) -> datetime:
        return payload.paid_at or datetime.utcnow()

    @staticmethod
    def _base_payment_record(
        *,
        bill: Bill,
        amount: Decimal,
        payment_method: str | None,
        reference_number: str | None,
        notes: str | None,
        paid_at: datetime | None,
        created_by: int | None,
        payment_type: PaymentType,
    ) -> Payment:
        return Payment(
            bill_id=bill.id,
            customer_id=bill.customer_id,
            supplier_id=bill.supplier_id,
            payment_direction=PaymentDirection.incoming if bill.bill_type == BillType.sell else PaymentDirection.outgoing,
            payment_type=payment_type,
            amount=FinancialService.money(amount),
            payment_method=PaymentService._payment_method(payment_method),
            reference_number=reference_number,
            notes=notes,
            paid_at=paid_at or datetime.utcnow(),
            created_by=created_by,
        )

    @staticmethod
    def create_initial_payment(
        *,
        db: Session,
        bill: Bill,
        amount: Decimal,
        payment_method: str | None,
        notes: str | None,
        created_by: int | None,
        paid_at: datetime | None,
    ) -> Payment:
        payment = PaymentService._base_payment_record(
            bill=bill,
            amount=amount,
            payment_method=payment_method,
            reference_number=None,
            notes=notes,
            paid_at=paid_at,
            created_by=created_by,
            payment_type=PaymentType.bill_initial_payment,
        )
        db.add(payment)
        return payment

    @staticmethod
    def _get_bill_for_payment(db: Session, bill_id: int) -> Bill:
        bill = (
            db.query(Bill)
            .options(joinedload(Bill.customer), joinedload(Bill.supplier))
            .filter(Bill.id == bill_id)
            .with_for_update()
            .first()
        )
        if not bill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bill with id {bill_id} not found")
        return bill

    @staticmethod
    def _get_open_bills_for_customer(db: Session, customer_id: int) -> list[Bill]:
        return (
            db.query(Bill)
            .filter(
                Bill.customer_id == customer_id,
                Bill.bill_type == BillType.sell,
                Bill.finalized_at.isnot(None),
                Bill.payment_status != PaymentStatus.paid,
            )
            .order_by(Bill.created_at.asc(), Bill.id.asc())
            .with_for_update()
            .all()
        )

    @staticmethod
    def _get_open_bills_for_supplier(db: Session, supplier_id: int) -> list[Bill]:
        return (
            db.query(Bill)
            .filter(
                Bill.supplier_id == supplier_id,
                Bill.bill_type == BillType.buy,
                Bill.finalized_at.isnot(None),
                Bill.payment_status != PaymentStatus.paid,
            )
            .order_by(Bill.created_at.asc(), Bill.id.asc())
            .with_for_update()
            .all()
        )

    @staticmethod
    def _allocate_payment(
        *,
        db: Session,
        bills: list[Bill],
        amount: Decimal,
        payment_method: str | None,
        reference_number: str | None,
        notes: str | None,
        paid_at: datetime | None,
        created_by: int | None,
        payment_type: PaymentType,
    ) -> list[Payment]:
        remaining = FinancialService.money(amount)
        outstanding = sum((FinancialService.money(bill.due_amount) for bill in bills), ZERO)
        outstanding = FinancialService.money(outstanding)

        if not bills or outstanding <= ZERO:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No outstanding bills found for payment")
        if remaining > outstanding:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment amount exceeds outstanding balance")

        created_payments: list[Payment] = []
        for bill in bills:
            if remaining <= ZERO:
                break

            allocation = min(FinancialService.money(bill.due_amount), remaining)
            if allocation <= ZERO:
                continue

            FinancialService.apply_payment_to_bill(bill=bill, amount=allocation)
            payment = PaymentService._base_payment_record(
                bill=bill,
                amount=allocation,
                payment_method=payment_method,
                reference_number=reference_number,
                notes=notes,
                paid_at=paid_at,
                created_by=created_by,
                payment_type=payment_type,
            )
            db.add(payment)
            created_payments.append(payment)
            remaining = FinancialService.money(remaining - allocation)

        return created_payments

    @staticmethod
    def record_customer_payment(db: Session, payload: CustomerDuePaymentCreate, current_user: User) -> PaymentCreateResult:
        customer = CustomerService.get_customer(db, payload.customer_id)

        if payload.bill_id is not None:
            bill = PaymentService._get_bill_for_payment(db, payload.bill_id)
            if bill.bill_type != BillType.sell or bill.customer_id != customer.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bill does not belong to this customer")
            bills = [bill]
        else:
            bills = PaymentService._get_open_bills_for_customer(db, customer.id)

        payments = PaymentService._allocate_payment(
            db=db,
            bills=bills,
            amount=payload.amount,
            payment_method=payload.payment_method,
            reference_number=payload.reference_number,
            notes=payload.notes,
            paid_at=payload.paid_at,
            created_by=current_user.id,
            payment_type=PaymentType.customer_payment,
        )
        FinancialService.recalculate_customer_due_balance(db, customer.id)
        db.commit()
        for payment in payments:
            db.refresh(payment)
        return PaymentCreateResult(
            payments=payments,
            total_allocated_amount=FinancialService.sum_payments(payments),
        )

    @staticmethod
    def record_supplier_payment(db: Session, payload: SupplierPayablePaymentCreate, current_user: User) -> PaymentCreateResult:
        supplier = SupplierService.get_supplier(db, payload.supplier_id)

        if payload.bill_id is not None:
            bill = PaymentService._get_bill_for_payment(db, payload.bill_id)
            if bill.bill_type != BillType.buy or bill.supplier_id != supplier.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bill does not belong to this supplier")
            bills = [bill]
        else:
            bills = PaymentService._get_open_bills_for_supplier(db, supplier.id)

        payments = PaymentService._allocate_payment(
            db=db,
            bills=bills,
            amount=payload.amount,
            payment_method=payload.payment_method,
            reference_number=payload.reference_number,
            notes=payload.notes,
            paid_at=payload.paid_at,
            created_by=current_user.id,
            payment_type=PaymentType.supplier_payment,
        )
        FinancialService.recalculate_supplier_payable_balance(db, supplier.id)
        db.commit()
        for payment in payments:
            db.refresh(payment)
        return PaymentCreateResult(
            payments=payments,
            total_allocated_amount=FinancialService.sum_payments(payments),
        )

    @staticmethod
    def add_bill_payment(db: Session, bill_id: int, payload: PaymentCreate, current_user: User) -> PaymentCreateResult:
        bill = PaymentService._get_bill_for_payment(db, bill_id)
        FinancialService.apply_payment_to_bill(bill=bill, amount=payload.amount)
        payment = PaymentService._base_payment_record(
            bill=bill,
            amount=payload.amount,
            payment_method=payload.payment_method,
            reference_number=payload.reference_number,
            notes=payload.notes,
            paid_at=payload.paid_at,
            created_by=current_user.id,
            payment_type=PaymentType.customer_payment if bill.bill_type == BillType.sell else PaymentType.supplier_payment,
        )
        db.add(payment)

        if bill.customer_id:
            FinancialService.recalculate_customer_due_balance(db, bill.customer_id)
        if bill.supplier_id:
            FinancialService.recalculate_supplier_payable_balance(db, bill.supplier_id)

        db.commit()
        db.refresh(payment)
        return PaymentCreateResult(payments=[payment], total_allocated_amount=FinancialService.money(payment.amount))

    @staticmethod
    def list_bill_payments(db: Session, bill_id: int) -> list[Payment]:
        PaymentService._get_bill_for_payment(db, bill_id)
        return (
            db.query(Payment)
            .filter(Payment.bill_id == bill_id)
            .order_by(Payment.paid_at.desc(), Payment.created_at.desc(), Payment.id.desc())
            .all()
        )

    @staticmethod
    def list_customer_payments(db: Session, customer_id: int) -> list[Payment]:
        CustomerService.get_customer(db, customer_id)
        return (
            db.query(Payment)
            .filter(Payment.customer_id == customer_id)
            .order_by(Payment.paid_at.desc(), Payment.created_at.desc(), Payment.id.desc())
            .all()
        )

    @staticmethod
    def list_supplier_payments(db: Session, supplier_id: int) -> list[Payment]:
        SupplierService.get_supplier(db, supplier_id)
        return (
            db.query(Payment)
            .filter(Payment.supplier_id == supplier_id)
            .order_by(Payment.paid_at.desc(), Payment.created_at.desc(), Payment.id.desc())
            .all()
        )

    @staticmethod
    def customer_summary(db: Session, customer_id: int) -> CustomerDueSummaryResponse:
        CustomerService.get_customer(db, customer_id)
        bills = (
            db.query(Bill)
            .filter(Bill.customer_id == customer_id, Bill.bill_type == BillType.sell, Bill.finalized_at.isnot(None))
            .all()
        )
        return CustomerDueSummaryResponse(
            customer_id=customer_id,
            total_billed=FinancialService.money(sum((bill.total_amount for bill in bills), ZERO)),
            total_paid=FinancialService.money(sum((bill.paid_amount for bill in bills), ZERO)),
            total_outstanding=FinancialService.money(sum((bill.due_amount for bill in bills), ZERO)),
            unpaid_bills_count=sum(1 for bill in bills if bill.payment_status == PaymentStatus.unpaid),
            partially_paid_bills_count=sum(1 for bill in bills if bill.payment_status == PaymentStatus.partially_paid),
        )

    @staticmethod
    def supplier_summary(db: Session, supplier_id: int) -> SupplierPayableSummaryResponse:
        SupplierService.get_supplier(db, supplier_id)
        bills = (
            db.query(Bill)
            .filter(Bill.supplier_id == supplier_id, Bill.bill_type == BillType.buy, Bill.finalized_at.isnot(None))
            .all()
        )
        return SupplierPayableSummaryResponse(
            supplier_id=supplier_id,
            total_purchased=FinancialService.money(sum((bill.total_amount for bill in bills), ZERO)),
            total_paid=FinancialService.money(sum((bill.paid_amount for bill in bills), ZERO)),
            total_outstanding=FinancialService.money(sum((bill.due_amount for bill in bills), ZERO)),
            unpaid_bills_count=sum(1 for bill in bills if bill.payment_status == PaymentStatus.unpaid),
            partially_paid_bills_count=sum(1 for bill in bills if bill.payment_status == PaymentStatus.partially_paid),
        )

    @staticmethod
    def customer_ledger(db: Session, customer_id: int) -> CustomerLedgerResponse:
        customer = CustomerService.get_customer(db, customer_id)
        bills = (
            db.query(Bill)
            .filter(Bill.customer_id == customer_id, Bill.bill_type == BillType.sell, Bill.finalized_at.isnot(None))
            .order_by(Bill.created_at.asc(), Bill.id.asc())
            .all()
        )
        payments = (
            db.query(Payment)
            .filter(Payment.customer_id == customer_id)
            .order_by(Payment.paid_at.asc(), Payment.id.asc())
            .all()
        )

        entries: list[LedgerEntryResponse] = []
        running_balance = ZERO
        for bill in bills:
            running_balance = FinancialService.money(running_balance + bill.total_amount)
            entries.append(
                LedgerEntryResponse(
                    entry_type="bill",
                    bill_id=bill.id,
                    bill_code=bill.bill_code,
                    amount=FinancialService.money(bill.total_amount),
                    paid_amount=FinancialService.money(bill.paid_amount),
                    due_amount=FinancialService.money(bill.due_amount),
                    total_amount=FinancialService.money(bill.total_amount),
                    payment_status=bill.payment_status.value,
                    notes=bill.notes,
                    happened_at=bill.finalized_at or bill.created_at,
                    running_balance=running_balance,
                )
            )

        for payment in payments:
            running_balance = FinancialService.money(running_balance - payment.amount)
            bill = next((candidate for candidate in bills if candidate.id == payment.bill_id), None)
            entries.append(
                LedgerEntryResponse(
                    entry_type="payment",
                    bill_id=payment.bill_id,
                    bill_code=bill.bill_code if bill else None,
                    payment_id=payment.id,
                    payment_type=payment.payment_type.value,
                    payment_method=payment.payment_method.value,
                    payment_direction=payment.payment_direction.value,
                    amount=FinancialService.money(payment.amount),
                    notes=payment.notes,
                    reference_number=payment.reference_number,
                    happened_at=payment.paid_at,
                    running_balance=running_balance,
                )
            )

        entries.sort(key=lambda entry: (entry.happened_at, 0 if entry.entry_type == "bill" else 1, entry.bill_id or 0, entry.payment_id or 0))
        running_balance = ZERO
        recomputed_entries: list[LedgerEntryResponse] = []
        for entry in entries:
            if entry.entry_type == "bill":
                running_balance = FinancialService.money(running_balance + entry.amount)
            else:
                running_balance = FinancialService.money(running_balance - entry.amount)
            recomputed_entries.append(entry.model_copy(update={"running_balance": running_balance}))

        return CustomerLedgerResponse(
            customer_id=customer.id,
            customer_name=customer.full_name,
            phone_number=customer.phone_number,
            email=customer.email,
            address=customer.address,
            is_active=customer.is_active,
            summary=PaymentService.customer_summary(db, customer.id),
            entries=recomputed_entries,
        )

    @staticmethod
    def supplier_ledger(db: Session, supplier_id: int) -> SupplierLedgerResponse:
        supplier = SupplierService.get_supplier(db, supplier_id)
        bills = (
            db.query(Bill)
            .filter(Bill.supplier_id == supplier_id, Bill.bill_type == BillType.buy, Bill.finalized_at.isnot(None))
            .order_by(Bill.created_at.asc(), Bill.id.asc())
            .all()
        )
        payments = (
            db.query(Payment)
            .filter(Payment.supplier_id == supplier_id)
            .order_by(Payment.paid_at.asc(), Payment.id.asc())
            .all()
        )

        entries: list[LedgerEntryResponse] = []
        running_balance = ZERO
        for bill in bills:
            running_balance = FinancialService.money(running_balance + bill.total_amount)
            entries.append(
                LedgerEntryResponse(
                    entry_type="bill",
                    bill_id=bill.id,
                    bill_code=bill.bill_code,
                    amount=FinancialService.money(bill.total_amount),
                    paid_amount=FinancialService.money(bill.paid_amount),
                    due_amount=FinancialService.money(bill.due_amount),
                    total_amount=FinancialService.money(bill.total_amount),
                    payment_status=bill.payment_status.value,
                    notes=bill.notes,
                    happened_at=bill.finalized_at or bill.created_at,
                    running_balance=running_balance,
                )
            )

        for payment in payments:
            running_balance = FinancialService.money(running_balance - payment.amount)
            bill = next((candidate for candidate in bills if candidate.id == payment.bill_id), None)
            entries.append(
                LedgerEntryResponse(
                    entry_type="payment",
                    bill_id=payment.bill_id,
                    bill_code=bill.bill_code if bill else None,
                    payment_id=payment.id,
                    payment_type=payment.payment_type.value,
                    payment_method=payment.payment_method.value,
                    payment_direction=payment.payment_direction.value,
                    amount=FinancialService.money(payment.amount),
                    notes=payment.notes,
                    reference_number=payment.reference_number,
                    happened_at=payment.paid_at,
                    running_balance=running_balance,
                )
            )

        entries.sort(key=lambda entry: (entry.happened_at, 0 if entry.entry_type == "bill" else 1, entry.bill_id or 0, entry.payment_id or 0))
        running_balance = ZERO
        recomputed_entries: list[LedgerEntryResponse] = []
        for entry in entries:
            if entry.entry_type == "bill":
                running_balance = FinancialService.money(running_balance + entry.amount)
            else:
                running_balance = FinancialService.money(running_balance - entry.amount)
            recomputed_entries.append(entry.model_copy(update={"running_balance": running_balance}))

        return SupplierLedgerResponse(
            supplier_id=supplier.id,
            supplier_name=supplier.supplier_name,
            phone_number=supplier.phone_number,
            email=supplier.email,
            address=supplier.address,
            is_active=supplier.is_active,
            summary=PaymentService.supplier_summary(db, supplier.id),
            entries=recomputed_entries,
        )

    @staticmethod
    def dashboard_due_summary(db: Session) -> DueDashboardSummaryResponse:
        finalized_bills = db.query(Bill).filter(Bill.finalized_at.isnot(None)).all()
        recent_payments = db.query(Payment).order_by(Payment.paid_at.desc(), Payment.id.desc()).limit(10).all()

        customer_due_map: dict[int, tuple[Customer, Decimal, int]] = {}
        supplier_payable_map: dict[int, tuple[Supplier, Decimal, int]] = {}

        for bill in finalized_bills:
            if bill.bill_type == BillType.sell and bill.customer_id and FinancialService.money(bill.due_amount) > ZERO and bill.customer:
                current_balance, current_count = customer_due_map.get(bill.customer_id, (bill.customer, ZERO, 0))[1:]
                customer_due_map[bill.customer_id] = (
                    bill.customer,
                    FinancialService.money(current_balance + bill.due_amount),
                    current_count + 1,
                )
            if bill.bill_type == BillType.buy and bill.supplier_id and FinancialService.money(bill.due_amount) > ZERO and bill.supplier:
                current_balance, current_count = supplier_payable_map.get(bill.supplier_id, (bill.supplier, ZERO, 0))[1:]
                supplier_payable_map[bill.supplier_id] = (
                    bill.supplier,
                    FinancialService.money(current_balance + bill.due_amount),
                    current_count + 1,
                )

        top_customers = sorted(customer_due_map.values(), key=lambda entry: entry[1], reverse=True)[:5]
        top_suppliers = sorted(supplier_payable_map.values(), key=lambda entry: entry[1], reverse=True)[:5]

        return DueDashboardSummaryResponse(
            total_customer_dues=FinancialService.money(
                sum((bill.due_amount for bill in finalized_bills if bill.bill_type == BillType.sell), ZERO)
            ),
            total_supplier_payables=FinancialService.money(
                sum((bill.due_amount for bill in finalized_bills if bill.bill_type == BillType.buy), ZERO)
            ),
            unpaid_sell_bills_count=sum(
                1 for bill in finalized_bills if bill.bill_type == BillType.sell and bill.payment_status == PaymentStatus.unpaid
            ),
            unpaid_buy_bills_count=sum(
                1 for bill in finalized_bills if bill.bill_type == BillType.buy and bill.payment_status == PaymentStatus.unpaid
            ),
            partially_paid_bills_count=sum(1 for bill in finalized_bills if bill.payment_status == PaymentStatus.partially_paid),
            recent_payments=recent_payments,
            top_customers_with_dues=[
                DashboardPartyBalance(
                    id=customer.id,
                    name=customer.full_name,
                    phone_number=customer.phone_number,
                    balance=FinancialService.money(balance),
                    bills_count=bills_count,
                )
                for customer, balance, bills_count in top_customers
            ],
            top_suppliers_with_payables=[
                DashboardPartyBalance(
                    id=supplier.id,
                    name=supplier.supplier_name,
                    phone_number=supplier.phone_number,
                    balance=FinancialService.money(balance),
                    bills_count=bills_count,
                )
                for supplier, balance, bills_count in top_suppliers
            ],
        )
