from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fast_api.auth.authlib.permissions import require_permission, Permission
from fast_api.db import get_db
from fast_api.config import get_settings
from fast_api.services.retention_service import RetentionService
from fast_api.models.user import User

router = APIRouter(prefix="/retention", tags=["retention"])
settings = get_settings()


@router.post("/purge-audit-logs")
async def purge_expired_audit_logs(
    current_user: User = Depends(require_permission(Permission.RETENTION_EXECUTE)),
    db: AsyncSession = Depends(get_db),
):
    service = RetentionService(db)
    deleted = await service.purge_expired_audit_logs(settings.AUDIT_LOG_RETENTION_DAYS)
    return {
        "message": "Audit log purge completed",
        "deleted_count": deleted,
        "retention_days": settings.AUDIT_LOG_RETENTION_DAYS,
    }
