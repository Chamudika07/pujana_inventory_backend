from pydantic import BaseModel 
from datetime import datetime
from app.schemas import category
from decimal import Decimal 


class ItemBase(BaseModel):
    name: str
    quantity: int
    buying_price : Decimal
    selling_price : Decimal
    description: str | None = None
    model_number: str
    
    
class ItemCreate(ItemBase):
    category_id : int
    pass

class ItemOut(ItemBase):
    id: int
    created_at: datetime
    category : category.CategoryOut
    

    class Config:
        from_attributes = True