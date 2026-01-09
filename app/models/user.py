from sqlalchemy import TIMESTAMP , Column, Integer, String 
from sqlalchemy.sql.expression import null , text
from app.database import Base



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True , nullable=False)
    email = Column(String, unique=True,  nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('now()'))