from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Boolean
from sqlalchemy.sql import func
from datetime import datetime
from fast_api.db import Base
import enum


class MSISDNStatus(str, enum.Enum):
    ACTIVE = "active"
    RECYCLED = "recycled"
    CONFLICTED = "conflicted"
    BLOCKED = "blocked"
    AVAILABLE = "available"


class CleanupStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RecycledSIM(Base):
    """Recycled SIM card model."""

    __tablename__ = "recycled_sims"

    id = Column(Integer, primary_key=True, index=True)
    sim_serial = Column(String(50), unique=True, nullable=False, index=True)
    msisdn = Column(String(20), unique=True, nullable=False, index=True)
    imsi = Column(String(20), nullable=False, index=True)
    operator_code = Column(String(10), nullable=False, index=True)
    date_recycled = Column(DateTime(timezone=True), nullable=False)
    date_deactivated = Column(DateTime(timezone=True), nullable=True)
    previous_owner_nin = Column(String(20), nullable=True, index=True)
    new_registration_status = Column(String(50), nullable=True)
    previous_nin_linked = Column(Boolean, default=False, nullable=False)
    previous_bvn_linked = Column(Boolean, default=False, nullable=False)
    msisdn_status = Column(
        SQLEnum(MSISDNStatus), default=MSISDNStatus.RECYCLED, nullable=False
    )
    cleanup_status = Column(
        SQLEnum(CleanupStatus), default=CleanupStatus.PENDING, nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<RecycledSIM(id={self.id}, msisdn={self.msisdn}, sim_serial={self.sim_serial})>"
