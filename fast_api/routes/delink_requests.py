from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from fast_api.auth.authlib.oauth2 import get_current_user
from fast_api.auth.authlib.rbac import require_role
from fast_api.db import get_db
from fast_api.exceptions import ValidationError, ResourceNotFoundError
from fast_api.exceptions.handlers import to_http_exception
from fast_api.schemas.delink_request import (
    DelinkRequestCreate,
    DelinkRequestResponse,
    DelinkRequestApprove,
)
from fast_api.schemas.common import PaginatedResponse
from fast_api.services.delink_service import DelinkService
from fast_api.models.user import User
from fast_api.models.delink_request import DelinkRequestType

router = APIRouter(prefix="/delink-requests", tags=["delink_requests"])


@router.get("", response_model=PaginatedResponse)
async def get_delink_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = DelinkService(db)
        filters = {}
        if status:
            filters["status"] = status

        requests = await service.get_all_delink_requests(
            skip=skip, limit=limit, filters=filters
        )
        total = await service.count_delink_requests(filters=filters)

        return PaginatedResponse(
            items=[DelinkRequestResponse.model_validate(req) for req in requests],
            total=total,
            skip=skip,
            limit=limit,
        )
    except ValidationError as e:
        raise to_http_exception(e)


@router.post("", response_model=DelinkRequestResponse)
async def create_delink_request(
    request_in: DelinkRequestCreate,
    current_user: User = Depends(require_role(["admin", "operator"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        try:
            request_type = DelinkRequestType(request_in.request_type)
        except ValueError:
            raise ValidationError(
                f"Invalid request_type: {request_in.request_type}",
                details={"valid_types": [t.value for t in DelinkRequestType]},
            )

        service = DelinkService(db)
        delink_request = await service.create_delink_request(
            recycled_sim_id=request_in.recycled_sim_id,
            request_type=request_type,
            initiated_by=current_user.id,
            reason=request_in.reason,
        )
        return DelinkRequestResponse.model_validate(delink_request)
    except (ValidationError, ResourceNotFoundError) as e:
        raise to_http_exception(e)


@router.get("/{request_id}", response_model=DelinkRequestResponse)
async def get_delink_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from fast_api.exceptions import AuthorizationError
    try:
        service = DelinkService(db)
        delink_request = await service.get_delink_request_by_id(request_id)
        if not delink_request:
            raise ResourceNotFoundError("DelinkRequest", request_id)
        if (
            delink_request.initiated_by != current_user.id
            and current_user.role not in ("admin", "auditor")
        ):
            raise AuthorizationError("You do not have access to this delink request")
        return DelinkRequestResponse.model_validate(delink_request)
    except (ResourceNotFoundError, AuthorizationError) as e:
        raise to_http_exception(e)


@router.post("/{request_id}/approve", response_model=DelinkRequestResponse)
async def approve_delink_request(
    request_id: int,
    approval: DelinkRequestApprove,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = DelinkService(db)
        if approval.approved:
            delink_request = await service.approve_delink_request(
                request_id, current_user.id
            )
        else:
            delink_request = await service.reject_delink_request(
                request_id, current_user.id, reason=getattr(approval, "reason", "Rejected by admin")
            )

        return DelinkRequestResponse.model_validate(delink_request)
    except (ValidationError, ResourceNotFoundError) as e:
        raise to_http_exception(e)


@router.post("/{request_id}/cancel", response_model=DelinkRequestResponse)
async def cancel_delink_request(
    request_id: int,
    current_user: User = Depends(require_role(["admin", "operator"])),
    db: AsyncSession = Depends(get_db),
):
    from fast_api.exceptions import AuthorizationError
    try:
        service = DelinkService(db)
        existing = await service.get_delink_request_by_id(request_id)
        if not existing:
            raise ResourceNotFoundError("DelinkRequest", request_id)
        if existing.initiated_by != current_user.id and current_user.role != "admin":
            raise AuthorizationError("You can only cancel your own delink requests")
        delink_request = await service.cancel_delink_request(request_id)
        return DelinkRequestResponse.model_validate(delink_request)
    except (ValidationError, ResourceNotFoundError, AuthorizationError) as e:
        raise to_http_exception(e)
