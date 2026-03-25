from __future__ import annotations

import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, JSON, Text
from sqlalchemy.sql import func
from fast_api.db import Base


class StakeholderType(str, enum.Enum):
    NIMC = "nimc"
    NIBSS = "nibss"
    TELECOM = "telecom"
    BANK = "bank"


class StakeholderStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class Stakeholder(Base):
    __tablename__ = "stakeholders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    stakeholder_type = Column(Enum(StakeholderType), nullable=False)
    status = Column(Enum(StakeholderStatus), default=StakeholderStatus.ACTIVE, nullable=False)

    api_base_url = Column(String(500), nullable=False)
    auth_method = Column(String(50), default="bearer", nullable=False)
    auth_credentials_ref = Column(String(255), nullable=True)

    supported_operations = Column(JSON, default=list)
    rate_limit_per_minute = Column(Integer, default=60)
    timeout_seconds = Column(Integer, default=30)

    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_status = Column(String(50), nullable=True)
    last_sync_records = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
