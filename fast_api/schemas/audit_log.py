from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from typing import Any
from datetime import datetime


class AuditLogResponse(BaseModel):
    """Audit log response schema."""

    id: int
    user_id: int | None = None
    action: str
    resource_type: str
    resource_id: str
    old_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
