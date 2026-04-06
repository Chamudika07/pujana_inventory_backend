from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.customer import CustomerBasic
from app.schemas.supplier import SupplierBasic


Money = Decimal


class BillCreateItem(BaseModel):
    model_number: str = Field(min_length=1)
    quantity: int = Field(gt=0)

    @field_validator("model_number")
    @classmethod
    def normalize_model_number(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("model_number cannot be empty")
        return normalized


class BillCreate(BaseModel):
    bill_type: Literal["buy", "sell"]
    items: List[BillCreateItem] = Field(min_length=1)
    customer_id: Optional[int] = Field(default=None, gt=0)
    supplier_id: Optional[int] = Field(default=None, gt=0)
    discount_amount: Money = Field(default=Decimal("0"), ge=Decimal("0"))
    tax_amount: Money = Field(default=Decimal("0"), ge=Decimal("0"))
    initial_paid_amount: Money = Field(default=Decimal("0"), ge=Decimal("0"))
    payment_method: Optional[str] = None
    payment_mode_summary: Optional[str] = None
    notes: Optional[str] = None
    finalized_at: Optional[datetime] = None

    @field_validator("payment_mode_summary", "notes")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_parties(self):
        if self.bill_type == "sell" and self.supplier_id is not None:
            raise ValueError("supplier_id can only be used with buy bills")
        if self.bill_type == "buy" and self.customer_id is not None:
            raise ValueError("customer_id can only be used with sell bills")
        return self


class BillFinalize(BillCreate):
    pass


class PaymentSummary(BaseModel):
    id: int
    amount: Money
    payment_method: str
    payment_type: str
    payment_direction: str
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    paid_at: datetime
    created_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


class BillLineItemResponse(BaseModel):
    id: int
    item_id: int
    item_name: str
    model_number: str
    quantity: int
    unit_price: Money
    line_total: Money
    transaction_type: str
    created_at: datetime


class BillResponse(BaseModel):
    id: int
    bill_id: str
    bill_code: str
    bill_type: Literal["buy", "sell"]
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    customer: Optional[CustomerBasic] = None
    supplier: Optional[SupplierBasic] = None
    subtotal_amount: Money
    discount_amount: Money
    tax_amount: Money
    total_amount: Money
    paid_amount: Money
    due_amount: Money
    payment_status: str
    payment_mode_summary: Optional[str] = None
    notes: Optional[str] = None
    finalized_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BillDetailResponse(BillResponse):
    items: List[BillLineItemResponse]
    payments: List[PaymentSummary]


class StartBillResponse(BaseModel):
    bill_id: str
    bill_type: Literal["buy", "sell"]
    message: str


class BillCreateResponse(StartBillResponse):
    total_items: int
    subtotal_amount: Money
    discount_amount: Money
    tax_amount: Money
    total_amount: Money
    paid_amount: Money
    due_amount: Money
    payment_status: str
