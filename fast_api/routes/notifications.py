from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from fast_api.auth.authlib.oauth2 import get_current_user
from fast_api.auth.authlib.rbac import require_role
from fast_api.db import get_db
from fast_api.exceptions import ValidationError, ResourceNotFoundError
from fast_api.exceptions.handlers import to_http_exception
from fast_api.schemas.notification import (
    NotificationResponse,
    NotificationSendRequest,
)
from fast_api.schemas.common import PaginatedResponse
from fast_api.services.notification_service import NotificationService
from fast_api.models.notification import (
    NotificationRecipientType,
    NotificationChannel,
)
from fast_api.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=PaginatedResponse)
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    channel: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = NotificationService(db)
        filters = {}
        if status:
            filters["status"] = status
        if channel:
            filters["channel"] = channel

        notifications = await service.get_all_notifications(
            skip=skip, limit=limit, filters=filters
        )
        total = await service.count_notifications(filters=filters)

        return PaginatedResponse(
            items=[NotificationResponse.model_validate(n) for n in notifications],
            total=total,
            skip=skip,
            limit=limit,
        )
    except ValidationError as e:
        raise to_http_exception(e)


@router.post("", response_model=NotificationResponse)
async def send_notification(
    request: NotificationSendRequest,
    current_user: User = Depends(require_role(["admin", "operator"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = NotificationService(db)
        notification = await service.create_notification(
            delink_request_id=request.delink_request_id,
            recipient_type=NotificationRecipientType(request.recipient_type),
            channel=NotificationChannel(request.channel),
            recipient_address=request.recipient_address,
            message_template=request.message_template,
        )
        return NotificationResponse.model_validate(notification)
    except (ValidationError, ResourceNotFoundError) as e:
        raise to_http_exception(e)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    current_user: User = Depends(require_role(["admin", "operator", "auditor"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = NotificationService(db)
        notification = await service.get_notification_by_id(notification_id)
        if not notification:
            raise ResourceNotFoundError("Notification", notification_id)
        return NotificationResponse.model_validate(notification)
    except ResourceNotFoundError as e:
        raise to_http_exception(e)
