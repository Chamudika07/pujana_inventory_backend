from pydantic import BaseModel 
from datetime import datetime
from app.schemas import category


class ItemBase(BaseModel):
    name: str
    description: str | None = None
    model_number: str
    
    
class ItemCreate(ItemBase):
    category_id : int
    pass

class ItemOut(ItemBase):
    id: int
    name: str
    description: str | None = None
    model_number: str 
    created_at: datetime
    category : category.CategoryOut
    

    class Config:
        from_attributes = True