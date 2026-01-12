from pydantic import BaseModel 
from datetime import datetime
from decimal import Decimal


class InventoryTransaction(BaseModel):
    item_id : int
    transaction_type = str
    quantity : int
    buying_price = Decimal
    selling_price = Decimal
    

class InventoryTransactionCreate(InventoryTransaction):
    pass 


class InventoryTransactionOut(InventoryTransaction):
    id : int
    created_at: datetime
    
    class Config:
        from_attributes = True