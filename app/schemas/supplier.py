from datetime import datetime
from decimal import Decimal
import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


def normalize_supplier_phone_number(phone_number: str) -> str:
    phone_number = phone_number.strip()
    if not phone_number:
        return phone_number

    has_plus = phone_number.startswith("+")
    digits = re.sub(r"\D", "", phone_number)
    if not digits:
        return ""

    return f"+{digits}" if has_plus else digits


class SupplierBase(BaseModel):
    supplier_name: str = Field(min_length=1, max_length=255)
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone_number: str = Field(min_length=1, max_length=30)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True

    @field_validator("supplier_name")
    @classmethod
    def validate_supplier_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("supplier_name cannot be empty")
        return normalized

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        normalized = normalize_supplier_phone_number(value)
        if not normalized:
            raise ValueError("phone_number cannot be empty")
        return normalized

    @field_validator("company_name", "contact_person", "address", "notes")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone_number: Optional[str] = Field(default=None, min_length=1, max_length=30)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("supplier_name")
    @classmethod
    def validate_supplier_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("supplier_name cannot be empty")
        return normalized

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = normalize_supplier_phone_number(value)
        if not normalized:
            raise ValueError("phone_number cannot be empty")
        return normalized

    @field_validator("company_name", "contact_person", "address", "notes")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class SupplierSummary(BaseModel):
    number_of_purchase_bills: int
    total_purchased_amount: Decimal
    payable_balance: Decimal
    total_paid: Decimal = Decimal("0")


class SupplierListItem(BaseModel):
    id: int
    supplier_name: str
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone_number: str
    email: Optional[EmailStr] = None
    payable_balance: Decimal
    is_active: bool
    created_at: datetime
    summary: SupplierSummary


class SupplierDetailResponse(SupplierListItem):
    address: Optional[str] = None
    notes: Optional[str] = None
    updated_at: datetime


class SupplierBasic(BaseModel):
    id: int
    supplier_name: str
    phone_number: str
    company_name: Optional[str] = None
    email: Optional[EmailStr] = None

    class Config:
        from_attributes = True
