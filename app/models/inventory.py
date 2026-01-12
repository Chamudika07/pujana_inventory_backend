from sqlalchemy import TIMESTAMP , Column, Integer, String , Numeric
from sqlalchemy.sql.expression import null , text
from app.models.base import Base
from app.models.category import Category
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey


#create table
class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    
    id = Column(Integer , primary_key = True , nullable = False)
    item_id = Column(Integer , ForeignKey("items.id" , ondelete = "CASCADE" ) , nullable = False)
    transaction_type = Column(String , nullable = False) #buy/sell
    quantity = Column(Integer , nullable = False)
    buying_price = Column(Numeric(10, 2) , nullable = False)
    selling_price = Column(Numeric(10, 2) , nullable = False)
    transaction_date = Column(TIMESTAMP , nullable = False , server_default = text('now()')) 
    
    items = relationship("Item" , back_populates= "inventory_transactions")