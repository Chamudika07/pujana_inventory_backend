import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer, Numeric, String, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from app.models.base import Base


class BillType(str, enum.Enum):
    buy = "buy"
    sell = "sell"


class PaymentStatus(str, enum.Enum):
    unpaid = "unpaid"
    partially_paid = "partially_paid"
    paid = "paid"


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, nullable=False)
    bill_code = Column(String, unique=True, nullable=False, index=True)
    bill_type = Column(Enum(BillType), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True)
    subtotal_amount = Column(Numeric(12, 2), nullable=False, server_default="0")
    discount_amount = Column(Numeric(12, 2), nullable=False, server_default="0")
    tax_amount = Column(Numeric(12, 2), nullable=False, server_default="0")
    total_amount = Column(Numeric(12, 2), nullable=False, server_default="0")
    paid_amount = Column(Numeric(12, 2), nullable=False, server_default="0")
    due_amount = Column(Numeric(12, 2), nullable=False, server_default="0")
    payment_status = Column(Enum(PaymentStatus), nullable=False, server_default=PaymentStatus.unpaid.value, index=True)
    payment_mode_summary = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    finalized_at = Column(TIMESTAMP, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(TIMESTAMP, server_default=text("now()"))

    inventory_transactions = relationship("InventoryTransaction", back_populates="bill", cascade="all, delete")
    payments = relationship("Payment", back_populates="bill", cascade="all, delete-orphan", order_by="Payment.paid_at")
    customer = relationship("Customer", back_populates="bills")
    supplier = relationship("Supplier", back_populates="bills")
    creator = relationship("User")

    @property
    def bill_id(self):
        return self.bill_code
