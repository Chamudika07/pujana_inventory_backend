from pydantic import BaseModel 
from datetime import datetime
from decimal import Decimal
from typing import Literal 

class BillBase(BaseModel):
    bill_id : str
    bill_type : str
    created_at : datetime
    
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
    pass 

    class Config:
        from_attributes = True


class StartBillResponse(BaseModel):
    bill_id: str
    bill_type: Literal["buy", "sell"]
    message: str
 