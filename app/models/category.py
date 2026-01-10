from sqlalchemy import TIMESTAMP , Column, Integer, String 
from sqlalchemy.sql.expression import null , text
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True , nullable=False)
    name = Column(String, unique=True,  nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('now()'))