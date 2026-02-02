from sqlalchemy import TIMESTAMP , Column, Integer, String , ForeignKey , Boolean
from sqlalchemy.sql.expression import text
from app.models.base import Base
from sqlalchemy.orm import relationship


class LowStockAlert(Base):
    __tablename__ = "low_stock_alerts"
    
    id = Column(Integer, primary_key=True, nullable=False)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quantity_at_alert = Column(Integer, nullable=False)
    alert_type = Column(String, nullable=False)  # EMAIL, WHATSAPP, BOTH
    is_resolved = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('now()'))
    last_sent_at = Column(TIMESTAMP, nullable=True)
    next_alert_at = Column(TIMESTAMP, nullable=True)  # When to send next alert (24 hours later)
    
    item = relationship("Item", back_populates="low_stock_alerts")
    user = relationship("User")
