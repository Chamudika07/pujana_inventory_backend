from sqlalchemy import TIMESTAMP , Column, Integer, String 
from sqlalchemy.sql.expression import null , text
from app.models.base import Base
from app.models.category import Category


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True , nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    model_number = Column(String, nullable=True)
    category_id = Column
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('now()'))