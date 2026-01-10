from sqlalchemy import TIMESTAMP , Column, Integer, String  
from sqlalchemy.sql.expression import null , text
from app.models.base import Base
from sqlalchemy.orm import relationship


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True , nullable=False)
    name = Column(String, unique=True,  nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('now()'))

    items = relationship("Item", back_populates="category")