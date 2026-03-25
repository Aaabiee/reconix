from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fast_api.auth.authlib.oauth2 import get_current_user
from fast_api.auth.authlib.rbac import require_role
from fast_api.db import get_db, get_read_db
from fast_api.exceptions import ValidationError
from fast_api.exceptions.handlers import to_http_exception
from fast_api.services.corroboration_service import CorroborationService
from fast_api.validators.nigerian import NigerianValidators
from fast_api.models.user import User
from fast_api.middleware.rate_limiter import limiter

router = APIRouter(prefix="/identity", tags=["identity_mapping"])


@router.get("/lookup")
@limiter.limit("30/minute")
async def lookup_identity(
    request: Request,
    msisdn: str = Query(..., min_length=11, max_length=14),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_read_db),
):
    try:
        msisdn = NigerianValidators.normalize_msisdn(msisdn)
        service = CorroborationService(db)
        mapping = await service.get_identity_mapping(msisdn)
        return mapping.to_dict()
    except (ValidationError, ValueError) as e:
        raise to_http_exception(
            ValidationError(str(e)) if isinstance(e, ValueError) else e
        )


@router.get("/msisdn/{msisdn}/status")
@limiter.limit("60/minute")
async def get_msisdn_status(
    request: Request,
    msisdn: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_read_db),
):
    from sqlalchemy import select, func
    from fast_api.models.recycled_sim import RecycledSIM
    from fast_api.models.nin_linkage import NINLinkage
    from fast_api.models.bvn_linkage import BVNLinkage

    try:
        msisdn = NigerianValidators.normalize_msisdn(msisdn)
    except (ValidationError, ValueError) as e:
        raise to_http_exception(
            ValidationError(str(e)) if isinstance(e, ValueError) else e
        )

    sim_result = await db.execute(
        select(RecycledSIM).where(RecycledSIM.msisdn == msisdn)
    )
    sim = sim_result.scalar_one_or_none()

    nin_count = (await db.execute(
        select(func.count(NINLinkage.id)).where(
            NINLinkage.msisdn == msisdn, NINLinkage.is_active == True,
        )
    )).scalar() or 0

    bvn_count = (await db.execute(
        select(func.count(BVNLinkage.id)).where(
            BVNLinkage.msisdn == msisdn, BVNLinkage.is_active == True,
        )
    )).scalar() or 0

    is_recycled = sim is not None
    has_active_linkages = nin_count > 0 or bvn_count > 0

    if is_recycled and has_active_linkages:
        status = "CONFLICTED"
        can_assign = False
    elif is_recycled and not has_active_linkages:
        status = "AVAILABLE"
        can_assign = True
    elif not is_recycled and has_active_linkages:
        status = "ACTIVE"
        can_assign = False
    else:
        status = "AVAILABLE"
        can_assign = True

    return {
        "msisdn": msisdn,
        "status": status,
        "is_recycled": is_recycled,
        "active_nin_linkages": nin_count,
        "active_bvn_linkages": bvn_count,
        "can_assign_to_new_user": can_assign,
        "cleanup_status": sim.cleanup_status if sim else None,
        "operator_code": sim.operator_code if sim else None,
    }


@router.get("/msisdn/{msisdn}/linkages")
@limiter.limit("60/minute")
async def get_msisdn_linkages(
    request: Request,
    msisdn: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_read_db),
):
    from sqlalchemy import select
    from fast_api.models.nin_linkage import NINLinkage
    from fast_api.models.bvn_linkage import BVNLinkage

    try:
        msisdn = NigerianValidators.normalize_msisdn(msisdn)
    except (ValidationError, ValueError) as e:
        raise to_http_exception(
            ValidationError(str(e)) if isinstance(e, ValueError) else e
        )

    nin_result = await db.execute(
        select(NINLinkage).where(NINLinkage.msisdn == msisdn)
    )
    nin_linkages = nin_result.scalars().all()

    bvn_result = await db.execute(
        select(BVNLinkage).where(BVNLinkage.msisdn == msisdn)
    )
    bvn_linkages = bvn_result.scalars().all()

    return {
        "msisdn": msisdn,
        "nin_linkages": [
            {
                "nin": l.nin,
                "is_active": l.is_active,
                "source": l.source,
                "linked_date": l.linked_date.isoformat() if l.linked_date else None,
                "unlinked_date": l.unlinked_date.isoformat() if l.unlinked_date else None,
            }
            for l in nin_linkages
        ],
        "bvn_linkages": [
            {
                "bvn": l.bvn,
                "bank_code": l.bank_code,
                "is_active": l.is_active,
                "source": l.source,
                "linked_date": l.linked_date.isoformat() if l.linked_date else None,
                "unlinked_date": l.unlinked_date.isoformat() if l.unlinked_date else None,
            }
            for l in bvn_linkages
        ],
        "total_nin": len(nin_linkages),
        "total_bvn": len(bvn_linkages),
        "active_nin": sum(1 for l in nin_linkages if l.is_active),
        "active_bvn": sum(1 for l in bvn_linkages if l.is_active),
    }


@router.post("/batch-lookup")
@limiter.limit("10/minute")
async def batch_lookup_identities(
    request: Request,
    body: dict,
    current_user: User = Depends(require_role(["admin", "operator"])),
    db: AsyncSession = Depends(get_read_db),
):
    msisdns = body.get("msisdns", [])
    if not msisdns or not isinstance(msisdns, list):
        raise to_http_exception(ValidationError("msisdns must be a non-empty list"))

    if len(msisdns) > 100:
        raise to_http_exception(ValidationError("Maximum 100 MSISDNs per batch request"))

    try:
        service = CorroborationService(db)
        mappings = await service.get_batch_mappings(msisdns)
        return {
            "count": len(mappings),
            "mappings": [m.to_dict() for m in mappings],
        }
    except (ValidationError, ValueError) as e:
        raise to_http_exception(
            ValidationError(str(e)) if isinstance(e, ValueError) else e
        )


@router.get("/corroborate")
@limiter.limit("10/minute")
async def corroborate_identity(
    request: Request,
    msisdn: str = Query(..., min_length=11, max_length=14),
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        from fast_api.config import get_settings
        settings = get_settings()

        service = CorroborationService(db)

        nimc_adapter = None
        nibss_adapter = None

        if settings.NIMC_API_URL and settings.NIMC_API_URL != "https://api.nimc.gov.ng":
            from fast_api.services.adapters.nimc_adapter import NIMCAdapter
            nimc_adapter = NIMCAdapter(
                base_url=settings.NIMC_API_URL,
                timeout=settings.BANK_API_TIMEOUT,
            )

        if settings.NIBSS_API_URL and settings.NIBSS_API_URL != "https://api.nibss.gov.ng":
            from fast_api.services.adapters.nibss_adapter import NIBSSAdapter
            nibss_adapter = NIBSSAdapter(
                base_url=settings.NIBSS_API_URL,
                timeout=settings.BANK_API_TIMEOUT,
            )

        mapping = await service.corroborate_with_external(
            msisdn=msisdn,
            nimc_adapter=nimc_adapter,
            nibss_adapter=nibss_adapter,
        )
        return mapping.to_dict()
    except (ValidationError, ValueError) as e:
        raise to_http_exception(
            ValidationError(str(e)) if isinstance(e, ValueError) else e
        )


@router.get("/conflicts")
@limiter.limit("30/minute")
async def list_conflicts(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role(["admin", "auditor"])),
    db: AsyncSession = Depends(get_read_db),
):
    from sqlalchemy import select, func, or_
    from fast_api.models.nin_linkage import NINLinkage
    from fast_api.models.bvn_linkage import BVNLinkage
    from fast_api.models.recycled_sim import RecycledSIM

    nin_subq = (
        select(NINLinkage.msisdn)
        .where(NINLinkage.is_active == True)
        .group_by(NINLinkage.msisdn)
        .having(func.count(NINLinkage.id) > 1)
    )
    result = await db.execute(nin_subq.offset(skip).limit(limit))
    conflicted_msisdns = result.scalars().all()

    conflicts = []
    for msisdn in conflicted_msisdns:
        stmt = select(NINLinkage).where(
            NINLinkage.msisdn == msisdn,
            NINLinkage.is_active == True,
        )
        linkage_result = await db.execute(stmt)
        linkages = linkage_result.scalars().all()
        nins = list({l.nin for l in linkages})
        if len(nins) > 1:
            conflicts.append({
                "msisdn": msisdn,
                "type": "duplicate_nin",
                "values": nins,
                "count": len(linkages),
            })

    return {
        "total": len(conflicts),
        "conflicts": conflicts,
    }
