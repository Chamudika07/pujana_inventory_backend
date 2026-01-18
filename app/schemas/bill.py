from pydantic import BaseModel 
from datetime import datetime


class BillBase(BaseModel):
    bill_id : str
    bill_type : str
    created_at : datetime
    
class billOut(BillBase):
    pass 

    class Config:
        from_attributes = True
    