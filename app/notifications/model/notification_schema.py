from datetime import datetime

from pydantic import BaseModel, Field

from app.notifications.model.notification_channel import NotificationChannel
from app.notifications.model.notification_status import NotificationStatus


class NotificationCreate(BaseModel):
    content: str = Field(..., min_length=1)
    channel: NotificationChannel
    recipient: str = Field(..., min_length=1)
    scheduled_at: datetime
    timezone: str = Field(..., min_length=1)


class NotificationStatusUpdate(BaseModel):
    status: NotificationStatus


class NotificationResponse(BaseModel):
    id: int
    content: str
    channel: NotificationChannel
    recipient: str
    scheduled_at: datetime
    timezone: str
    status: NotificationStatus
    created_at: datetime
    idempotency_key: str

    model_config = {
        "from_attributes": True
    }