from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
from fast_api.db import Base
import enum


class BVNLinkageSource(str, enum.Enum):
    """Source of BVN linkage enumeration."""

    NIBSS_API = "nibss_api"
    MANUAL = "manual"
    BULK_UPLOAD = "bulk_upload"


class BVNLinkage(Base):
    """BVN (Bank Verification Number) linkage model."""

    __tablename__ = "bvn_linkages"

    id = Column(Integer, primary_key=True, index=True)
    msisdn = Column(String(20), nullable=False, index=True)
    bvn = Column(String(20), nullable=False, index=True)
    linked_date = Column(DateTime(timezone=True), nullable=False)
    unlinked_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    bank_code = Column(String(10), nullable=True)
    source = Column(
        SQLEnum(BVNLinkageSource), default=BVNLinkageSource.NIBSS_API, nullable=False
    )
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<BVNLinkage(id={self.id}, msisdn={self.msisdn}, bvn={self.bvn})>"
