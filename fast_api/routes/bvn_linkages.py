from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from fast_api.auth.authlib.oauth2 import get_current_user
from fast_api.db import get_db
from fast_api.exceptions import ValidationError
from fast_api.exceptions.handlers import to_http_exception
from fast_api.schemas.bvn_linkage import (
    BVNLinkageResponse,
    BVNVerifyRequest,
    BVNVerifyResponse,
    BVNBulkCheckRequest,
    BVNBulkCheckResponse,
)
from fast_api.schemas.common import PaginatedResponse
from fast_api.services.linkage_service import BVNLinkageService
from fast_api.models.user import User

router = APIRouter(prefix="/bvn-linkages", tags=["bvn_linkages"])


@router.get("", response_model=PaginatedResponse)
async def get_bvn_linkages(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = BVNLinkageService(db)
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active

        linkages = await service.get_all_linkages(skip=skip, limit=limit, filters=filters)
        total = await service.count_linkages(filters=filters)

        return PaginatedResponse(
            items=[BVNLinkageResponse.model_validate(linkage) for linkage in linkages],
            total=total,
            skip=skip,
            limit=limit,
        )
    except ValidationError as e:
        raise to_http_exception(e)


@router.post("/verify", response_model=BVNVerifyResponse)
async def verify_bvn_linkage(
    request: BVNVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = BVNLinkageService(db)
        linkage = await service.get_active_linkage_for_msisdn(request.msisdn)

        return BVNVerifyResponse(
            msisdn=request.msisdn,
            bvn=linkage.bvn if linkage else None,
            is_linked=linkage is not None,
            bank_code=linkage.bank_code if linkage else None,
            linked_since=linkage.linked_date if linkage else None,
            verified_at=linkage.verified_at if linkage else None,
        )
    except ValidationError as e:
        raise to_http_exception(e)


@router.post("/bulk-check", response_model=BVNBulkCheckResponse)
async def bulk_check_bvn_linkages(
    request: BVNBulkCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = BVNLinkageService(db)
        linkage_map = await service.batch_get_active_linkages(request.msisdns)

        results = []
        linked_count = 0

        for msisdn in request.msisdns:
            from fast_api.validators.nigerian import NigerianValidators
            normalized = NigerianValidators.normalize_msisdn(msisdn)
            linkage = linkage_map.get(normalized)
            is_linked = linkage is not None
            if is_linked:
                linked_count += 1

            results.append(
                BVNVerifyResponse(
                    msisdn=msisdn,
                    bvn=linkage.bvn if linkage else None,
                    is_linked=is_linked,
                    bank_code=linkage.bank_code if linkage else None,
                    linked_since=linkage.linked_date if linkage else None,
                    verified_at=linkage.verified_at if linkage else None,
                )
            )

        return BVNBulkCheckResponse(
            total_checked=len(request.msisdns),
            linked_count=linked_count,
            unlinked_count=len(request.msisdns) - linked_count,
            results=results,
        )
    except ValidationError as e:
        raise to_http_exception(e)
