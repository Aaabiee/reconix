from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from fast_api.auth.authlib.oauth2 import get_current_user
from fast_api.db import get_db, get_read_db
from fast_api.exceptions import ValidationError
from fast_api.exceptions.handlers import to_http_exception
from fast_api.schemas.common import DashboardStats
from fast_api.models.recycled_sim import RecycledSIM, CleanupStatus
from fast_api.models.delink_request import DelinkRequest, DelinkRequestStatus
from fast_api.models.nin_linkage import NINLinkage
from fast_api.models.bvn_linkage import BVNLinkage
from fast_api.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_read_db),
):
    try:
        total_sims = (
            await db.execute(select(func.count(RecycledSIM.id)))
        ).scalar() or 0

        pending_sims = (
            await db.execute(
                select(func.count(RecycledSIM.id)).where(
                    RecycledSIM.cleanup_status == CleanupStatus.PENDING
                )
            )
        ).scalar() or 0

        in_progress_sims = (
            await db.execute(
                select(func.count(RecycledSIM.id)).where(
                    RecycledSIM.cleanup_status == CleanupStatus.IN_PROGRESS
                )
            )
        ).scalar() or 0

        completed_sims = (
            await db.execute(
                select(func.count(RecycledSIM.id)).where(
                    RecycledSIM.cleanup_status == CleanupStatus.COMPLETED
                )
            )
        ).scalar() or 0

        failed_sims = (
            await db.execute(
                select(func.count(RecycledSIM.id)).where(
                    RecycledSIM.cleanup_status == CleanupStatus.FAILED
                )
            )
        ).scalar() or 0

        active_nin = (
            await db.execute(
                select(func.count(NINLinkage.id)).where(NINLinkage.is_active == True)
            )
        ).scalar() or 0

        active_bvn = (
            await db.execute(
                select(func.count(BVNLinkage.id)).where(BVNLinkage.is_active == True)
            )
        ).scalar() or 0

        total_delinks = (
            await db.execute(select(func.count(DelinkRequest.id)))
        ).scalar() or 0

        pending_delinks = (
            await db.execute(
                select(func.count(DelinkRequest.id)).where(
                    DelinkRequest.status == DelinkRequestStatus.PENDING
                )
            )
        ).scalar() or 0

        completed_delinks = (
            await db.execute(
                select(func.count(DelinkRequest.id)).where(
                    DelinkRequest.status == DelinkRequestStatus.COMPLETED
                )
            )
        ).scalar() or 0

        failed_delinks = (
            await db.execute(
                select(func.count(DelinkRequest.id)).where(
                    DelinkRequest.status == DelinkRequestStatus.FAILED
                )
            )
        ).scalar() or 0

        return DashboardStats(
            total_recycled_sims=total_sims,
            total_cleanup_pending=pending_sims,
            total_cleanup_in_progress=in_progress_sims,
            total_cleanup_completed=completed_sims,
            total_cleanup_failed=failed_sims,
            active_nin_linkages=active_nin,
            active_bvn_linkages=active_bvn,
            total_delink_requests=total_delinks,
            delink_pending=pending_delinks,
            delink_completed=completed_delinks,
            delink_failed=failed_delinks,
        )

    except ValidationError as e:
        raise to_http_exception(e)


@router.get("/trends")
async def get_dashboard_trends(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_read_db),
):
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    sims_created = (
        await db.execute(
            select(func.count(RecycledSIM.id)).where(
                RecycledSIM.created_at >= cutoff_date
            )
        )
    ).scalar() or 0

    delinks_created = (
        await db.execute(
            select(func.count(DelinkRequest.id)).where(
                DelinkRequest.created_at >= cutoff_date
            )
        )
    ).scalar() or 0

    return {
        "period_days": days,
        "sims_created_in_period": sims_created,
        "delinks_created_in_period": delinks_created,
        "start_date": cutoff_date.isoformat(),
        "end_date": datetime.now(timezone.utc).isoformat(),
    }
