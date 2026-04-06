import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer, Numeric, String, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from app.models.base import Base


class PaymentDirection(str, enum.Enum):
    incoming = "incoming"
    outgoing = "outgoing"


class PaymentType(str, enum.Enum):
    customer_payment = "customer_payment"
    supplier_payment = "supplier_payment"
    bill_initial_payment = "bill_initial_payment"


class PaymentMethod(str, enum.Enum):
    cash = "cash"
    card = "card"
    bank_transfer = "bank_transfer"
    cheque = "cheque"
    other = "other"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, nullable=False)
    bill_id = Column(Integer, ForeignKey("bills.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True)
    payment_direction = Column(Enum(PaymentDirection), nullable=False)
    payment_type = Column(Enum(PaymentType), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False, server_default=PaymentMethod.cash.value)
    reference_number = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    paid_at = Column(TIMESTAMP, nullable=False, server_default=text("now()"), index=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("now()"), index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    bill = relationship("Bill", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")
    supplier = relationship("Supplier", back_populates="payments")
    creator = relationship("User")
