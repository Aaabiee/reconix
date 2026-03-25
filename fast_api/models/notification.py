from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.sql import func
from datetime import datetime
from fast_api.db import Base
import enum


class NotificationRecipientType(str, enum.Enum):
    """Recipient type enumeration."""

    FORMER_OWNER = "former_owner"
    BANK = "bank"
    NIMC = "nimc"
    NEW_OWNER = "new_owner"
    NEXT_OF_KIN = "next_of_kin"
    NIBSS = "nibss"


class NotificationChannel(str, enum.Enum):
    """Notification channel enumeration."""

    SMS = "sms"
    EMAIL = "email"
    API_CALLBACK = "api_callback"


class NotificationStatus(str, enum.Enum):
    """Notification status enumeration."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class Notification(Base):
    """Notification model for alerting stakeholders."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    delink_request_id = Column(
        Integer, ForeignKey("delink_requests.id"), nullable=False, index=True
    )
    recipient_type = Column(
        SQLEnum(NotificationRecipientType),
        default=NotificationRecipientType.FORMER_OWNER,
        nullable=False,
    )
    channel = Column(
        SQLEnum(NotificationChannel),
        default=NotificationChannel.EMAIL,
        nullable=False,
    )
    recipient_address = Column(String(255), nullable=False)
    status = Column(
        SQLEnum(NotificationStatus),
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True,
    )
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    message_template = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, delink_request_id={self.delink_request_id}, status={self.status})>"
