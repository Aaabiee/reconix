from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime


class DataSubjectAccessRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    request_type: str = Field(
        ...,
        pattern="^(access|deletion|rectification|portability)$",
    )
    reason: str = Field("", max_length=1000)


class DataSubjectAccessResponse(BaseModel):
    request_id: str
    status: str
    request_type: str
    submitted_at: datetime
    estimated_completion: str


class PersonalDataExport(BaseModel):
    user_id: int
    email: str
    full_name: str
    role: str
    organization: str
    created_at: datetime
    last_login: datetime | None
    audit_log_count: int
    delink_requests_initiated: int
    data_retention_policy: str


class DataDeletionResponse(BaseModel):
    request_id: str
    status: str
    records_queued_for_deletion: int
    estimated_completion: str
    retention_notice: str
