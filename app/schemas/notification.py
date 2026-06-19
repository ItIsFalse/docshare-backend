from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationResponse(BaseModel):
    id: int
    type: str  # appointment | medication | alert | system | family
    title: str
    message: str
    read: bool
    created_at: datetime
    related_type: Optional[str] = None
    related_id: Optional[int] = None

    class Config:
        from_attributes = True


class NotificationUnreadCount(BaseModel):
    count: int


class PushTokenRegister(BaseModel):
    token: str
    platform: str  # android | ios