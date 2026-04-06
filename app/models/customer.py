from sqlalchemy import TIMESTAMP, Boolean, Column, Enum, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base


class CustomerType(str, enum.Enum):
    retail = "retail"
    wholesale = "wholesale"
    regular = "regular"
    vip = "vip"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, nullable=False)
    full_name = Column(String(255), nullable=False, index=True)
    phone_number = Column(String(30), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    address = Column(Text, nullable=True)
    customer_type = Column(Enum(CustomerType), nullable=False, server_default=CustomerType.retail.value)
    notes = Column(Text, nullable=True)
    loyalty_points = Column(Integer, nullable=False, server_default="0")
    due_balance = Column(Numeric(12, 2), nullable=False, server_default="0")
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    bills = relationship("Bill", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")
