from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class NotificationResponse(BaseModel):
    """Notification response schema."""

    id: int
    delink_request_id: int
    recipient_type: str
    channel: str
    recipient_address: str
    status: str
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    message_template: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationSendRequest(BaseModel):
    """Manual notification send request schema."""

    delink_request_id: int
    recipient_type: str = Field(..., pattern="^(former_owner|bank|nimc|new_owner)$")
    channel: str = Field(..., pattern="^(sms|email|api_callback)$")
    recipient_address: str
    message_template: str | None = None
