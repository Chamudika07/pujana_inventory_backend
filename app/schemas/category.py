from pydantic import BaseModel 
from datetime import datetime
from typing import Optional

class CategoryBase(BaseModel):
    name: str
    description: str | None = None
    
class CategoryCreate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True