from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from fast_api.auth.authlib.oauth2 import get_current_user
from fast_api.auth.authlib.rbac import require_role
from fast_api.db import get_db
from fast_api.exceptions import ValidationError
from fast_api.exceptions.handlers import to_http_exception
from fast_api.schemas.recycled_sim import (
    RecycledSIMCreate,
    RecycledSIMResponse,
    RecycledSIMUpdate,
    RecycledSIMBulkUpload,
    BulkUploadResponse,
)
from fast_api.schemas.common import PaginatedResponse
from fast_api.services.recycled_sim_service import RecycledSIMService
from fast_api.models.user import User

router = APIRouter(prefix="/recycled-sims", tags=["recycled_sims"])


@router.get("", response_model=PaginatedResponse)
async def get_recycled_sims(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    cleanup_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = RecycledSIMService(db)
        filters = {}
        if cleanup_status:
            filters["cleanup_status"] = cleanup_status

        sims = await service.get_all_sims(skip=skip, limit=limit, filters=filters)
        total = await service.count_sims(filters=filters)

        return PaginatedResponse(
            items=[RecycledSIMResponse.model_validate(sim) for sim in sims],
            total=total,
            skip=skip,
            limit=limit,
        )
    except ValidationError as e:
        raise to_http_exception(e)


@router.post("", response_model=RecycledSIMResponse)
async def create_recycled_sim(
    sim_in: RecycledSIMCreate,
    current_user: User = Depends(require_role(["admin", "operator"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = RecycledSIMService(db)
        sim = await service.create_sim(sim_in)
        return RecycledSIMResponse.model_validate(sim)
    except ValidationError as e:
        raise to_http_exception(e)


@router.post("/bulk", response_model=BulkUploadResponse)
async def bulk_upload_sims(
    bulk_in: RecycledSIMBulkUpload,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = RecycledSIMService(db)
        result = await service.create_bulk_sims(bulk_in.sims)
        return BulkUploadResponse(**result)
    except ValidationError as e:
        raise to_http_exception(e)


@router.get("/{sim_id}", response_model=RecycledSIMResponse)
async def get_recycled_sim(
    sim_id: int,
    current_user: User = Depends(require_role(["admin", "operator", "auditor"])),
    db: AsyncSession = Depends(get_db),
):
    from fast_api.exceptions import ResourceNotFoundError
    try:
        service = RecycledSIMService(db)
        sim = await service.get_sim_by_id(sim_id)
        if not sim:
            raise ResourceNotFoundError("RecycledSIM", sim_id)
        return RecycledSIMResponse.model_validate(sim)
    except (ValidationError, ResourceNotFoundError) as e:
        raise to_http_exception(e)


@router.patch("/{sim_id}", response_model=RecycledSIMResponse)
async def update_recycled_sim(
    sim_id: int,
    sim_in: RecycledSIMUpdate,
    current_user: User = Depends(require_role(["admin", "operator"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = RecycledSIMService(db)
        sim = await service.update_sim(sim_id, sim_in)
        return RecycledSIMResponse.model_validate(sim)
    except ValidationError as e:
        raise to_http_exception(e)


@router.post("/detect")
async def detect_recycled_sims(
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    from fast_api.models.recycled_sim import RecycledSIM, CleanupStatus, MSISDNStatus
    from fast_api.models.nin_linkage import NINLinkage
    from fast_api.models.bvn_linkage import BVNLinkage
    from sqlalchemy import select, func

    pending_sims = await db.execute(
        select(RecycledSIM).where(
            RecycledSIM.cleanup_status == CleanupStatus.PENDING,
        )
    )
    sims = pending_sims.scalars().all()

    flagged = 0
    clean = 0

    for sim in sims:
        nin_count = (await db.execute(
            select(func.count(NINLinkage.id)).where(
                NINLinkage.msisdn == sim.msisdn,
                NINLinkage.is_active == True,
            )
        )).scalar() or 0

        bvn_count = (await db.execute(
            select(func.count(BVNLinkage.id)).where(
                BVNLinkage.msisdn == sim.msisdn,
                BVNLinkage.is_active == True,
            )
        )).scalar() or 0

        has_nin = nin_count > 0
        has_bvn = bvn_count > 0

        if has_nin or has_bvn:
            sim.previous_nin_linked = has_nin
            sim.previous_bvn_linked = has_bvn
            sim.msisdn_status = MSISDNStatus.CONFLICTED
            flagged += 1
        else:
            sim.msisdn_status = MSISDNStatus.AVAILABLE
            clean += 1

    await db.commit()

    return {
        "message": "Detection scan completed",
        "total_scanned": len(sims),
        "conflicted": flagged,
        "clean": clean,
    }
