from pydantic import BaseModel 
from datetime import datetime
from decimal import Decimal
from typing import Literal , List
import enum

class BillType(str , enum.Enum):
    buy = "buy"
    sell = "sell"

class BillBase(BaseModel):
    bill_code : str
    bill_type : BillType
    created_at : datetime
    
class SellRequest(BaseModel):
    item_id: int
    quantity: int
    price: float

class BuyRequest(BaseModel):
    item_id: int
    quantity: int
    price: float
    
class BillItemAction(BaseModel):
    bill_id : str
    model_number : str
    quantity : int
    
class BillItemOut(BaseModel):
    bill_id : str
    item_id : int
    transaction_type : str
    price : Decimal
    
    class Config:
        from_attributes = True
    
class BillOut(BillBase):
    id : int
    bill_id : str

    class Config:
        from_attributes = True


class StartBillResponse(BaseModel):
    bill_id: str
    bill_type: Literal["buy", "sell"]
    message: str