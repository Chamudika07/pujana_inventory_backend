from sqlalchemy import TIMESTAMP , Column, Integer, String  , Numeric
from sqlalchemy.sql.expression import null , text
from app.models.base import Base
from app.models.category import Category
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

#creat teble
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True , nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Integer , nullable = False , server_default="0")
    buying_price = Column(Numeric(10, 2) , nullable = False)
    selling_price = Column(Numeric(10, 2) , nullable = False)
    description = Column(String, nullable=True)
    model_number = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id" , ondelete="CASCADE") ,nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('now()'))
    
    category = relationship("Category", back_populates = "items")
    inventory_transaction = relationship("InventoryTransaction" , back_populates = "items" , cascade = "all, delete")
    low_stock_alerts = relationship("LowStockAlert", back_populates="item", cascade="all, delete")
