from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


Money = Decimal
PAYMENT_METHOD_VALUES = {"cash", "card", "bank_transfer", "cheque", "other"}


class PaymentCreate(BaseModel):
    bill_id: Optional[int] = Field(default=None, gt=0)
    amount: Money = Field(gt=Decimal("0"))
    payment_method: Literal["cash", "card", "bank_transfer", "cheque", "other"] = "cash"
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None

    @field_validator("reference_number", "notes")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class CustomerDuePaymentCreate(PaymentCreate):
    customer_id: int = Field(gt=0)


class SupplierPayablePaymentCreate(PaymentCreate):
    supplier_id: int = Field(gt=0)


class PaymentResponse(BaseModel):
    id: int
    bill_id: int
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    payment_direction: str
    payment_type: str
    amount: Money
    payment_method: str
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    paid_at: datetime
    created_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


class PaymentCreateResult(BaseModel):
    payments: List[PaymentResponse]
    total_allocated_amount: Money


class LedgerPartyBase(BaseModel):
    id: int
    name: str
    phone_number: str
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: bool


class CustomerDueSummaryResponse(BaseModel):
    customer_id: int
    total_billed: Money
    total_paid: Money
    total_outstanding: Money
    unpaid_bills_count: int
    partially_paid_bills_count: int


class SupplierPayableSummaryResponse(BaseModel):
    supplier_id: int
    total_purchased: Money
    total_paid: Money
    total_outstanding: Money
    unpaid_bills_count: int
    partially_paid_bills_count: int


class LedgerEntryResponse(BaseModel):
    entry_type: Literal["bill", "payment"]
    bill_id: Optional[int] = None
    bill_code: Optional[str] = None
    payment_id: Optional[int] = None
    payment_type: Optional[str] = None
    payment_method: Optional[str] = None
    payment_direction: Optional[str] = None
    amount: Money
    paid_amount: Optional[Money] = None
    due_amount: Optional[Money] = None
    total_amount: Optional[Money] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None
    reference_number: Optional[str] = None
    happened_at: datetime
    running_balance: Money


class CustomerLedgerResponse(BaseModel):
    customer_id: int
    customer_name: str
    phone_number: str
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: bool
    summary: CustomerDueSummaryResponse
    entries: List[LedgerEntryResponse]


class SupplierLedgerResponse(BaseModel):
    supplier_id: int
    supplier_name: str
    phone_number: str
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: bool
    summary: SupplierPayableSummaryResponse
    entries: List[LedgerEntryResponse]


class DashboardPartyBalance(BaseModel):
    id: int
    name: str
    phone_number: Optional[str] = None
    balance: Money
    bills_count: int


class DueDashboardSummaryResponse(BaseModel):
    total_customer_dues: Money
    total_supplier_payables: Money
    unpaid_sell_bills_count: int
    unpaid_buy_bills_count: int
    partially_paid_bills_count: int
    recent_payments: List[PaymentResponse]
    top_customers_with_dues: List[DashboardPartyBalance]
    top_suppliers_with_payables: List[DashboardPartyBalance]
