from sqlalchemy import TIMESTAMP , Column, Integer, String 
from sqlalchemy.sql.expression import  text
from app.models.base import Base
from sqlalchemy.orm import relationship


class Bill(Base):
    __tablename__ = "bills"
    
    id = Column(Integer , primary_key = True , nullable = False)
    bill_id = Column(String , unique = True , nullable = False , index = True)
    bill_type = Column(String , nullable = False) #buy or Sell
    created_at = Column(TIMESTAMP , server_default = text("now()"))
    
    transactions = relationship("InventoryTransaction" , back_populates = "bill" , cascade = "all , delete")