from sqlalchemy import TIMESTAMP , Column, Integer, String , Boolean
from sqlalchemy.sql.expression import null , text
from app.models.base import Base



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True , nullable=False)
    email = Column(String, unique=True,  nullable=False)
    password = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    notification_email = Column(String, nullable=True)
    notification_enabled = Column(Boolean, nullable=False, server_default="true")
    alert_threshold = Column(Integer, nullable=False, server_default="5")
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('now()'))