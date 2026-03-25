from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any
from datetime import datetime, timezone
from fast_api.db import BaseRepository
from fast_api.models.nin_linkage import NINLinkage
from fast_api.models.bvn_linkage import BVNLinkage
from fast_api.exceptions import ResourceNotFoundError, ValidationError
from fast_api.validators.nigerian import NigerianValidators


class NINLinkageService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = BaseRepository(db, NINLinkage)

    async def create_linkage(
        self, msisdn: str, nin: str, source: str = "nimc_api"
    ) -> NINLinkage:
        msisdn = NigerianValidators.normalize_msisdn(msisdn)

        is_valid, error = NigerianValidators.validate_nin(nin)
        if not is_valid:
            raise ValidationError(f"Invalid NIN: {error}")

        linkage_data = {
            "msisdn": msisdn,
            "nin": nin,
            "linked_date": datetime.now(timezone.utc),
            "is_active": True,
            "source": source,
            "verified_at": datetime.now(timezone.utc),
        }

        linkage = await self.repository.create(linkage_data)
        await self.db.commit()
        return linkage

    async def get_active_linkage_for_msisdn(self, msisdn: str) -> NINLinkage | None:
        msisdn = NigerianValidators.normalize_msisdn(msisdn)
        stmt = select(NINLinkage).where(
            (NINLinkage.msisdn == msisdn) & (NINLinkage.is_active == True)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def batch_get_active_linkages(
        self, msisdns: list[str]
    ) -> dict[str, NINLinkage]:
        normalized = [NigerianValidators.normalize_msisdn(m) for m in msisdns]
        stmt = select(NINLinkage).where(
            NINLinkage.msisdn.in_(normalized),
            NINLinkage.is_active == True,
        )
        result = await self.db.execute(stmt)
        linkages = result.scalars().all()
        return {linkage.msisdn: linkage for linkage in linkages}

    async def unlink(self, linkage_id: int) -> NINLinkage | None:
        linkage = await self.repository.get_by_id(linkage_id)
        if not linkage:
            return None

        updated = await self.repository.update(
            linkage_id,
            {"is_active": False, "unlinked_date": datetime.now(timezone.utc)},
        )
        await self.db.commit()
        return updated

    async def get_all_linkages(
        self, skip: int = 0, limit: int = 50, filters: dict[str, Any] | None = None
    ) -> list[NINLinkage]:
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)

    async def count_linkages(
        self, filters: dict[str, Any] = None
    ) -> int:
        return await self.repository.count(filters=filters)


class BVNLinkageService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = BaseRepository(db, BVNLinkage)

    async def create_linkage(
        self,
        msisdn: str,
        bvn: str,
        bank_code: str | None = None,
        source: str = "nibss_api",
    ) -> BVNLinkage:
        msisdn = NigerianValidators.normalize_msisdn(msisdn)

        is_valid, error = NigerianValidators.validate_bvn(bvn)
        if not is_valid:
            raise ValidationError(f"Invalid BVN: {error}")

        linkage_data = {
            "msisdn": msisdn,
            "bvn": bvn,
            "bank_code": bank_code,
            "linked_date": datetime.now(timezone.utc),
            "is_active": True,
            "source": source,
            "verified_at": datetime.now(timezone.utc),
        }

        linkage = await self.repository.create(linkage_data)
        await self.db.commit()
        return linkage

    async def get_active_linkage_for_msisdn(self, msisdn: str) -> BVNLinkage | None:
        msisdn = NigerianValidators.normalize_msisdn(msisdn)
        stmt = select(BVNLinkage).where(
            (BVNLinkage.msisdn == msisdn) & (BVNLinkage.is_active == True)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def batch_get_active_linkages(
        self, msisdns: list[str]
    ) -> dict[str, BVNLinkage]:
        normalized = [NigerianValidators.normalize_msisdn(m) for m in msisdns]
        stmt = select(BVNLinkage).where(
            BVNLinkage.msisdn.in_(normalized),
            BVNLinkage.is_active == True,
        )
        result = await self.db.execute(stmt)
        linkages = result.scalars().all()
        return {linkage.msisdn: linkage for linkage in linkages}

    async def unlink(self, linkage_id: int) -> BVNLinkage | None:
        linkage = await self.repository.get_by_id(linkage_id)
        if not linkage:
            return None

        updated = await self.repository.update(
            linkage_id,
            {"is_active": False, "unlinked_date": datetime.now(timezone.utc)},
        )
        await self.db.commit()
        return updated

    async def get_all_linkages(
        self, skip: int = 0, limit: int = 50, filters: dict[str, Any] | None = None
    ) -> list[BVNLinkage]:
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)

    async def count_linkages(
        self, filters: dict[str, Any] = None
    ) -> int:
        return await self.repository.count(filters=filters)
