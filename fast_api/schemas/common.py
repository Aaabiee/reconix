from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from typing import TypeVar, Generic, Any

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    code: str
    message: str
    details: dict[str, Any] | None = None


class PaginationParams(BaseModel):
    """Pagination parameters."""

    skip: int = 0
    limit: int = 50


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    """Dashboard statistics."""

    total_recycled_sims: int
    total_cleanup_pending: int
    total_cleanup_in_progress: int
    total_cleanup_completed: int
    total_cleanup_failed: int
    active_nin_linkages: int
    active_bvn_linkages: int
    total_delink_requests: int
    delink_pending: int
    delink_completed: int
    delink_failed: int
