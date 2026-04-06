from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bill import Bill, BillType, PaymentStatus
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.supplier import Supplier


ZERO = Decimal("0.00")


class FinancialService:
    @staticmethod
    def money(value: Decimal | int | str | None) -> Decimal:
        return Decimal(value or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_total(*, subtotal_amount: Decimal, discount_amount: Decimal, tax_amount: Decimal) -> Decimal:
        subtotal_amount = FinancialService.money(subtotal_amount)
        discount_amount = FinancialService.money(discount_amount)
        tax_amount = FinancialService.money(tax_amount)

        if subtotal_amount < ZERO or discount_amount < ZERO or tax_amount < ZERO:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amounts cannot be negative")
        if discount_amount > subtotal_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="discount_amount cannot exceed subtotal_amount",
            )

        total_amount = subtotal_amount - discount_amount + tax_amount
        if total_amount < ZERO:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="total_amount cannot be negative")
        return FinancialService.money(total_amount)

    @staticmethod
    def payment_status(*, total_amount: Decimal, paid_amount: Decimal) -> PaymentStatus:
        total_amount = FinancialService.money(total_amount)
        paid_amount = FinancialService.money(paid_amount)

        if paid_amount <= ZERO:
            return PaymentStatus.unpaid
        if paid_amount < total_amount:
            return PaymentStatus.partially_paid
        return PaymentStatus.paid

    @staticmethod
    def validate_paid_amount(*, total_amount: Decimal, paid_amount: Decimal) -> None:
        total_amount = FinancialService.money(total_amount)
        paid_amount = FinancialService.money(paid_amount)
        if paid_amount < ZERO:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="paid_amount cannot be negative")
        if paid_amount > total_amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="paid_amount cannot exceed total_amount")

    @staticmethod
    def refresh_bill_financials(bill: Bill) -> Bill:
        bill.subtotal_amount = FinancialService.money(bill.subtotal_amount)
        bill.discount_amount = FinancialService.money(bill.discount_amount)
        bill.tax_amount = FinancialService.money(bill.tax_amount)
        bill.total_amount = FinancialService.calculate_total(
            subtotal_amount=bill.subtotal_amount,
            discount_amount=bill.discount_amount,
            tax_amount=bill.tax_amount,
        )
        bill.paid_amount = FinancialService.money(bill.paid_amount)
        FinancialService.validate_paid_amount(total_amount=bill.total_amount, paid_amount=bill.paid_amount)
        bill.due_amount = FinancialService.money(bill.total_amount - bill.paid_amount)
        bill.payment_status = FinancialService.payment_status(total_amount=bill.total_amount, paid_amount=bill.paid_amount)
        return bill

    @staticmethod
    def apply_payment_to_bill(*, bill: Bill, amount: Decimal) -> Bill:
        amount = FinancialService.money(amount)
        if amount <= ZERO:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment amount must be greater than zero")
        if bill.finalized_at is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only finalized bills can receive payments")
        if FinancialService.money(bill.due_amount) <= ZERO:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This bill is already fully paid")
        if amount > FinancialService.money(bill.due_amount):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment amount exceeds outstanding balance")

        bill.paid_amount = FinancialService.money(bill.paid_amount + amount)
        return FinancialService.refresh_bill_financials(bill)

    @staticmethod
    def recalculate_customer_due_balance(db: Session, customer_id: int) -> Decimal:
        due_balance = (
            db.query(func.coalesce(func.sum(Bill.due_amount), 0))
            .filter(Bill.customer_id == customer_id, Bill.bill_type == BillType.sell, Bill.finalized_at.isnot(None))
            .scalar()
        )
        value = FinancialService.money(due_balance)
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            customer.due_balance = value
        return value

    @staticmethod
    def recalculate_supplier_payable_balance(db: Session, supplier_id: int) -> Decimal:
        payable_balance = (
            db.query(func.coalesce(func.sum(Bill.due_amount), 0))
            .filter(Bill.supplier_id == supplier_id, Bill.bill_type == BillType.buy, Bill.finalized_at.isnot(None))
            .scalar()
        )
        value = FinancialService.money(payable_balance)
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if supplier:
            supplier.payable_balance = value
        return value

    @staticmethod
    def sum_payments(payments: Iterable[Payment]) -> Decimal:
        total = ZERO
        for payment in payments:
            total += FinancialService.money(payment.amount)
        return FinancialService.money(total)
