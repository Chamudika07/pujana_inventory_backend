from datetime import datetime
from decimal import Decimal
import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


CUSTOMER_TYPE_VALUES = {"retail", "wholesale", "regular", "vip"}


def normalize_phone_number(phone_number: str) -> str:
    phone_number = phone_number.strip()
    if not phone_number:
        return phone_number

    has_plus = phone_number.startswith("+")
    digits = re.sub(r"\D", "", phone_number)
    if not digits:
        return ""

    return f"+{digits}" if has_plus else digits


class CustomerBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    phone_number: str = Field(min_length=1, max_length=30)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    customer_type: str = "retail"
    notes: Optional[str] = None
    loyalty_points: int = Field(default=0, ge=0)
    is_active: bool = True

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("full_name cannot be empty")
        return normalized

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        normalized = normalize_phone_number(value)
        if not normalized:
            raise ValueError("phone_number cannot be empty")
        return normalized

    @field_validator("customer_type")
    @classmethod
    def validate_customer_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in CUSTOMER_TYPE_VALUES:
            raise ValueError("customer_type must be one of retail, wholesale, regular, vip")
        return normalized

    @field_validator("address", "notes")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    phone_number: Optional[str] = Field(default=None, min_length=1, max_length=30)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    customer_type: Optional[str] = None
    notes: Optional[str] = None
    loyalty_points: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("full_name cannot be empty")
        return normalized

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = normalize_phone_number(value)
        if not normalized:
            raise ValueError("phone_number cannot be empty")
        return normalized

    @field_validator("customer_type")
    @classmethod
    def validate_customer_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in CUSTOMER_TYPE_VALUES:
            raise ValueError("customer_type must be one of retail, wholesale, regular, vip")
        return normalized

    @field_validator("address", "notes")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class CustomerSummary(BaseModel):
    number_of_bills: int
    total_purchases: Decimal
    due_balance: Decimal
    total_paid: Decimal = Decimal("0")


class CustomerListItem(BaseModel):
    id: int
    full_name: str
    phone_number: str
    email: Optional[EmailStr] = None
    customer_type: str
    loyalty_points: int
    due_balance: Decimal
    is_active: bool
    created_at: datetime
    summary: CustomerSummary


class CustomerDetailResponse(CustomerListItem):
    address: Optional[str] = None
    notes: Optional[str] = None
    updated_at: datetime


class CustomerBasic(BaseModel):
    id: int
    full_name: str
    phone_number: str
    customer_type: str
    email: Optional[EmailStr] = None

    class Config:
        from_attributes = True
