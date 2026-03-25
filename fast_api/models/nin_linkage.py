from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
from fast_api.db import Base
import enum


class NINLinkageSource(str, enum.Enum):
    """Source of NIN linkage enumeration."""

    NIMC_API = "nimc_api"
    MANUAL = "manual"
    BULK_UPLOAD = "bulk_upload"


class NINLinkage(Base):
    """NIN (National Identification Number) linkage model."""

    __tablename__ = "nin_linkages"

    id = Column(Integer, primary_key=True, index=True)
    msisdn = Column(String(20), nullable=False, index=True)
    nin = Column(String(20), nullable=False, index=True)
    linked_date = Column(DateTime(timezone=True), nullable=False)
    unlinked_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    source = Column(
        SQLEnum(NINLinkageSource), default=NINLinkageSource.NIMC_API, nullable=False
    )
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<NINLinkage(id={self.id}, msisdn={self.msisdn}, nin={self.nin})>"
