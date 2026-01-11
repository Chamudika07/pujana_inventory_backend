from pydantic import BaseModel 
from datetime import datetime
from app.schemas import category


class ItemBase(BaseModel):
    name: str
    description: str | None = None
    model_number: str
    category_id : int
    
class ItemCreate(ItemBase):
    pass

class ItemOut(ItemBase):
    id: int
    name: str
    description: str | None = None
    model_number: str 
    category_id: category.CategoryOut
    created_at: datetime

    class Config:
        from_attributes = True