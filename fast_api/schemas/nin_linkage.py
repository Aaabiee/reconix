from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class NINLinkageResponse(BaseModel):
    """NIN linkage response schema."""

    id: int
    msisdn: str
    nin: str
    linked_date: datetime
    unlinked_date: datetime | None = None
    is_active: bool
    source: str
    verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NINVerifyRequest(BaseModel):
    """NIN verification request schema."""

    msisdn: str = Field(..., pattern=r"^\+?234[0-9]{10}$")


class NINVerifyResponse(BaseModel):
    """NIN verification response schema."""

    msisdn: str
    nin: str | None = None
    is_linked: bool
    linked_since: datetime | None = None
    verified_at: datetime | None = None


class NINBulkCheckRequest(BaseModel):
    """Bulk NIN check request schema."""

    msisdns: list[str] = Field(..., max_length=1000)


class NINBulkCheckResponse(BaseModel):
    """Bulk NIN check response schema."""

    total_checked: int
    linked_count: int
    unlinked_count: int
    results: list[NINVerifyResponse]
