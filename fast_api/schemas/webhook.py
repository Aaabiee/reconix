from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from datetime import datetime


class WebhookRegisterRequest(BaseModel):
    subscriber_name: str = Field(..., min_length=1, max_length=255)
    callback_url: HttpUrl
    events: list[str] = Field(default_factory=list)


class WebhookRegisterResponse(BaseModel):
    id: int
    subscriber_name: str
    callback_url: str
    events: list[str]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookReceiveRequest(BaseModel):
    source: str = Field(..., min_length=1, max_length=255)
    event_type: str = Field(..., min_length=1, max_length=100)
    payload: dict
    signature: str = Field(..., min_length=1)


class WebhookSubscriptionResponse(BaseModel):
    id: int
    subscriber_name: str
    callback_url: str
    events: list[str]
    is_active: bool
    user_id: int
    created_at: datetime
    last_triggered_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
