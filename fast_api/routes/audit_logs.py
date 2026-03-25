from __future__ import annotations

import re
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from fast_api.auth.authlib.rbac import require_role
from fast_api.db import get_db
from fast_api.exceptions import ValidationError
from fast_api.exceptions.handlers import to_http_exception
from fast_api.schemas.audit_log import AuditLogResponse
from fast_api.schemas.common import PaginatedResponse
from fast_api.services.audit_service import AuditService
from fast_api.models.user import User

router = APIRouter(prefix="/audit-logs", tags=["audit"])

RESOURCE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


@router.get("", response_model=PaginatedResponse)
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    current_user: User = Depends(require_role(["admin", "auditor"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = AuditService(db)
        filters = {}
        if action:
            filters["action"] = action
        if resource_type:
            filters["resource_type"] = resource_type

        logs = await service.get_all_audit_logs(
            skip=skip, limit=limit, filters=filters
        )
        total = await service.count_audit_logs(filters=filters)

        return PaginatedResponse(
            items=[AuditLogResponse.model_validate(log) for log in logs],
            total=total,
            skip=skip,
            limit=limit,
        )
    except ValidationError as e:
        raise to_http_exception(e)


@router.get("/resource/{resource_type}/{resource_id}", response_model=PaginatedResponse)
async def get_resource_audit_logs(
    resource_type: str,
    resource_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role(["admin", "auditor"])),
    db: AsyncSession = Depends(get_db),
):
    if not RESOURCE_ID_PATTERN.match(resource_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "resource_id must be alphanumeric, dashes, or underscores (max 64 chars)",
                "details": {},
            },
        )

    try:
        service = AuditService(db)
        logs = await service.get_logs_by_resource(
            resource_type=resource_type,
            resource_id=resource_id,
            skip=skip,
            limit=limit,
        )
        total = await service.count_audit_logs(
            filters={
                "resource_type": resource_type,
                "resource_id": resource_id,
            }
        )

        return PaginatedResponse(
            items=[AuditLogResponse.model_validate(log) for log in logs],
            total=total,
            skip=skip,
            limit=limit,
        )
    except ValidationError as e:
        raise to_http_exception(e)
