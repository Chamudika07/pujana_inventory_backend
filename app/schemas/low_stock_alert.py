from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.schemas.item import ItemOut
from app.schemas.user import UserOut


class LowStockAlertBase(BaseModel):
    item_id: int
    user_id: int
    quantity_at_alert: int
    alert_type: str


class LowStockAlertCreate(LowStockAlertBase):
    pass


class LowStockAlertOut(LowStockAlertBase):
    id: int
    is_resolved: bool
    created_at: datetime
    last_sent_at: Optional[datetime]
    next_alert_at: Optional[datetime]
    item: ItemOut
    
    class Config:
        from_attributes = True


class AlertStatsOut(BaseModel):
    total_alerts: int
    active_alerts: int
    resolved_alerts: int
    low_stock_items: int


class UserPreferencesUpdate(BaseModel):
    phone_number: Optional[str] = None
    notification_email: Optional[str] = None
    notification_enabled: Optional[bool] = None
    alert_threshold: Optional[int] = None
