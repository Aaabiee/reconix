from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class DelinkRequestCreate(BaseModel):
    """Delink request creation request schema."""

    recycled_sim_id: int
    request_type: str = Field(..., pattern="^(nin|bvn|both)$")
    reason: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DelinkRequestApprove(BaseModel):
    """Delink request approval request schema."""

    approved: bool
    reason: str | None = None


class DelinkRequestResponse(BaseModel):
    """Delink request response schema."""

    id: int
    recycled_sim_id: int
    request_type: str
    status: str
    initiated_by: int
    approved_by: int | None = None
    reason: str | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
