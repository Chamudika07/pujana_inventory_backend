from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.category import CategoryOut
from decimal import Decimal
from datetime import datetime


class ItemBase(BaseModel):
    name: str
    quantity: int = Field(default=0, ge=0)
    buying_price: Decimal
    selling_price: Decimal
    description: Optional[str] = None
    category_id: int


class ItemCreate(ItemBase):
    """Schema for creating item (model_number is auto-generated)"""
    pass


class ItemUpdate(BaseModel):
    """Schema for updating item (cannot update model_number)"""
    name: Optional[str] = None
    quantity: Optional[int] = None
    buying_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    description: Optional[str] = None
    category_id: Optional[int] = None


class ItemOut(ItemBase):
    """Schema for item response"""
    id: int
    model_number: str
    qr_code_path: Optional[str] = None
    category: CategoryOut
    created_at: datetime
    
    class Config:
        from_attributes = True