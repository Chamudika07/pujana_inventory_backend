from pydantic import BaseModel , Field
from datetime import datetime
from decimal import Decimal
from typing import Literal , Annotated , Optional

class InventoryTransaction(BaseModel):
    item_id : int
    transaction_type : Literal["buy" , "sell"]
    quantity : Annotated[int, Field(gt=0)]
    buying_price : Decimal
    selling_price : Decimal
    
class InventoryTransactionUpdate(InventoryTransaction):
    item_id : Optional[int] = None
    buying_price : Optional[Decimal] = None
    selling_price : Optional[Decimal] = None
    
class InventoryTransactionCreate(InventoryTransaction):
    pass 


class InventoryTransactionOut(InventoryTransaction):
    id : int
    created_at: datetime
    
    class Config:
        from_attributes = True