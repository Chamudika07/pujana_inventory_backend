from pydantic import BaseModel 
from datetime import datetime
from decimal import Decimal


class BillBase(BaseModel):
    bill_id : str
    bill_type : str
    created_at : datetime
    
class BillItemAction(BaseModel):
    bill_id : str
    model_number : str
    quantity : int
    
class BillItemOut(BillItemAction):
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
 
 