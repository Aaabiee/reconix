from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from fast_api.db import Base
from fast_api.crypto import EncryptedString


class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    subscriber_name = Column(String(255), nullable=False)
    callback_url = Column(String(500), nullable=False)
    secret_key = Column(EncryptedString(512), nullable=False)
    events = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
