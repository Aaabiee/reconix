from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class BVNLinkageResponse(BaseModel):
    """BVN linkage response schema."""

    id: int
    msisdn: str
    bvn: str
    linked_date: datetime
    unlinked_date: datetime | None = None
    is_active: bool
    bank_code: str | None = None
    source: str
    verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BVNVerifyRequest(BaseModel):
    """BVN verification request schema."""

    msisdn: str = Field(..., pattern=r"^\+?234[0-9]{10}$")


class BVNVerifyResponse(BaseModel):
    """BVN verification response schema."""

    msisdn: str
    bvn: str | None = None
    is_linked: bool
    bank_code: str | None = None
    linked_since: datetime | None = None
    verified_at: datetime | None = None


class BVNBulkCheckRequest(BaseModel):
    """Bulk BVN check request schema."""

    msisdns: list[str] = Field(..., max_length=1000)


class BVNBulkCheckResponse(BaseModel):
    """Bulk BVN check response schema."""

    total_checked: int
    linked_count: int
    unlinked_count: int
    results: list[BVNVerifyResponse]
