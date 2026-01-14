from pydantic import BaseModel , Field
from datetime import datetime
from decimal import Decimal
from typing import Literal , Annotated

class InventoryTransaction(BaseModel):
    item_id : int
    transaction_type : Literal["buy" , "sell"]
    quantity : Annotated[int, Field(gt=0)]
    buying_price : Decimal
    selling_price : Decimal
    
    
class InventoryTransactionCreate(InventoryTransaction):
    pass 


class InventoryTransactionOut(InventoryTransaction):
    id : int
    created_at: datetime
    
    class Config:
        from_attributes = True