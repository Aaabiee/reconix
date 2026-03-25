from __future__ import annotations

import secrets
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fast_api.auth.authlib.oauth2 import get_current_user
from fast_api.auth.authlib.api_key import verify_api_key
from fast_api.auth.authlib.rbac import require_role
from fast_api.db import get_db, BaseRepository
from fast_api.exceptions import ResourceNotFoundError, ValidationError
from fast_api.exceptions.handlers import to_http_exception
from fast_api.schemas.webhook import (
    WebhookRegisterRequest,
    WebhookRegisterResponse,
    WebhookReceiveRequest,
    WebhookSubscriptionResponse,
)
from fast_api.schemas.common import PaginatedResponse
from fast_api.models.webhook import WebhookSubscription
from fast_api.models.user import User
from fast_api.services.sync_service import SyncService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/register", response_model=WebhookRegisterResponse)
async def register_webhook(
    request: WebhookRegisterRequest,
    current_user: User = Depends(require_role(["admin", "operator"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        repo = BaseRepository(db, WebhookSubscription)
        webhook_data = {
            "subscriber_name": request.subscriber_name,
            "callback_url": str(request.callback_url),
            "secret_key": secrets.token_urlsafe(32),
            "events": request.events,
            "is_active": True,
            "user_id": current_user.id,
        }
        subscription = await repo.create(webhook_data)
        await db.commit()
        return WebhookRegisterResponse.model_validate(subscription)
    except ValidationError as e:
        raise to_http_exception(e)


@router.post("/receive")
async def receive_webhook(
    request: WebhookReceiveRequest,
    current_user: User = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    import json
    from fast_api.exceptions import AuthenticationError
    try:
        repo = BaseRepository(db, WebhookSubscription)
        subs = await repo.get_all(filters={"is_active": True})

        payload_bytes = json.dumps(request.payload, sort_keys=True, default=str).encode("utf-8")
        signature_valid = False
        for sub in subs:
            if SyncService.validate_webhook_signature(payload_bytes, request.signature, sub.secret_key):
                signature_valid = True
                break

        if not signature_valid:
            raise AuthenticationError("Invalid webhook signature")

        service = SyncService(db)
        result = await service.receive_update(
            source=request.source,
            payload=request.payload,
        )
        return result
    except AuthenticationError as e:
        raise to_http_exception(e)
    except ValidationError as e:
        raise to_http_exception(e)


@router.get("/subscriptions", response_model=PaginatedResponse)
async def list_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(db, WebhookSubscription)
    user_filter = {} if current_user.role == "admin" else {"user_id": current_user.id}
    subscriptions = await repo.get_all(skip=skip, limit=limit, filters=user_filter)
    total = await repo.count(filters=user_filter)

    return PaginatedResponse(
        items=[WebhookSubscriptionResponse.model_validate(s) for s in subscriptions],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: int,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        repo = BaseRepository(db, WebhookSubscription)
        subscription = await repo.get_by_id(subscription_id)
        if not subscription:
            raise ResourceNotFoundError("WebhookSubscription", subscription_id)

        await repo.update(subscription_id, {"is_active": False})
        await db.commit()
        return {"message": "Subscription deactivated", "id": subscription_id}
    except ResourceNotFoundError as e:
        raise to_http_exception(e)
