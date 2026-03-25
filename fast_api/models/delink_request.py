from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.sql import func
from datetime import datetime
from fast_api.db import Base
import enum


class DelinkRequestType(str, enum.Enum):
    """Type of delink request enumeration."""

    NIN = "nin"
    BVN = "bvn"
    BOTH = "both"


class DelinkRequestStatus(str, enum.Enum):
    """Status of delink request enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DelinkRequest(Base):
    """Delink request model for removing stale linkages."""

    __tablename__ = "delink_requests"

    id = Column(Integer, primary_key=True, index=True)
    recycled_sim_id = Column(
        Integer, ForeignKey("recycled_sims.id"), nullable=False, index=True
    )
    request_type = Column(
        SQLEnum(DelinkRequestType), default=DelinkRequestType.BOTH, nullable=False
    )
    status = Column(
        SQLEnum(DelinkRequestStatus),
        default=DelinkRequestStatus.PENDING,
        nullable=False,
        index=True,
    )
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reason = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<DelinkRequest(id={self.id}, recycled_sim_id={self.recycled_sim_id}, status={self.status})>"
