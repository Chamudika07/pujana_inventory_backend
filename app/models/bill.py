from sqlalchemy import TIMESTAMP , Column, Enum , ForeignKey , Integer , String 
from sqlalchemy.sql.expression import  text
from app.models.base import Base
from sqlalchemy.orm import relationship
import enum

class BillType(str , enum.Enum):
    buy = "buy"
    sell = "sell"


class Bill(Base):
    __tablename__ = "bills"
    
    id = Column(Integer , primary_key = True , nullable = False)
    bill_code = Column(String , unique = True , nullable = False , index = True)
    bill_type = Column(Enum(BillType) , nullable = False) #buy or Sell
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(TIMESTAMP , server_default = text("now()"))
    
    inventory_transactions = relationship("InventoryTransaction" , back_populates = "bill" , cascade="all, delete")
    customer = relationship("Customer", back_populates="bills")
    supplier = relationship("Supplier", back_populates="bills")

    @property
    def bill_id(self):
        return self.bill_code
