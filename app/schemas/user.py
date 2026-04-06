from pydantic import BaseModel, EmailStr , conint #import for data validation and settings management using python type annotations
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    phone_number: str | None = None
    notification_email: str | None = None
    
class UserOut(BaseModel):
    id: int
    email: EmailStr
    phone_number: str | None = None
    notification_email: str | None = None
    notification_enabled: bool
    alert_threshold: int
    created_at: datetime

    class Config:
        from_attributes = True
