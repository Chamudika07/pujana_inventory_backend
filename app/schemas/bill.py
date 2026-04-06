from pydantic import BaseModel, Field 
from datetime import datetime
from decimal import Decimal
from typing import Literal , List, Optional
import enum
from app.schemas.customer import CustomerBasic
from app.schemas.supplier import SupplierBasic

class BillType(str , enum.Enum):
    buy = "buy"
    sell = "sell"

class BillBase(BaseModel):
    bill_code : str
    bill_type : BillType
    created_at : datetime
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    
class BillCreateItem(BaseModel):
    model_number: str
    quantity: int = Field(gt=0)


class BillCreateRequest(BaseModel):
    bill_type: Literal["buy", "sell"]
    items: List[BillCreateItem]
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    
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
    customer: Optional[CustomerBasic] = None
    supplier: Optional[SupplierBasic] = None

    class Config:
        from_attributes = True


class StartBillResponse(BaseModel):
    bill_id: str
    bill_type: Literal["buy", "sell"]
    message: str


class BillCreateResponse(StartBillResponse):
    total_items: int
