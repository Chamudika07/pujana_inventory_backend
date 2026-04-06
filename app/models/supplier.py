from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from app.models.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, nullable=False)
    supplier_name = Column(String(255), nullable=False, index=True)
    company_name = Column(String(255), nullable=True, index=True)
    contact_person = Column(String(255), nullable=True)
    phone_number = Column(String(30), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    payable_balance = Column(Numeric(12, 2), nullable=False, server_default="0")
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    bills = relationship("Bill", back_populates="supplier")
