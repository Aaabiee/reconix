from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any
from fast_api.db import BaseRepository
from fast_api.models.recycled_sim import RecycledSIM, CleanupStatus
from fast_api.schemas.recycled_sim import RecycledSIMCreate, RecycledSIMUpdate
from fast_api.exceptions import ResourceNotFoundError, ValidationError
from fast_api.validators.nigerian import NigerianValidators


class RecycledSIMService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = BaseRepository(db, RecycledSIM)

    async def create_sim(self, sim_in: RecycledSIMCreate) -> RecycledSIM:
        is_valid, error = NigerianValidators.validate_msisdn(sim_in.msisdn)
        if not is_valid:
            raise ValidationError(f"Invalid MSISDN: {error}")

        is_valid, error = NigerianValidators.validate_imsi(sim_in.imsi)
        if not is_valid:
            raise ValidationError(f"Invalid IMSI: {error}")

        sim_data = sim_in.model_dump()
        sim_data["msisdn"] = NigerianValidators.normalize_msisdn(sim_data["msisdn"])

        sim = await self.repository.create(sim_data)
        await self.db.commit()
        return sim

    async def create_bulk_sims(self, sims_in: list[RecycledSIMCreate]) -> dict[str, Any]:
        successful = 0
        failed = 0
        errors = []

        async with self.db.begin_nested():
            for idx, sim_in in enumerate(sims_in):
                try:
                    is_valid, error = NigerianValidators.validate_msisdn(sim_in.msisdn)
                    if not is_valid:
                        raise ValidationError(f"Invalid MSISDN: {error}")

                    is_valid, error = NigerianValidators.validate_imsi(sim_in.imsi)
                    if not is_valid:
                        raise ValidationError(f"Invalid IMSI: {error}")

                    sim_data = sim_in.model_dump()
                    sim_data["msisdn"] = NigerianValidators.normalize_msisdn(sim_data["msisdn"])
                    await self.repository.create(sim_data)
                    successful += 1
                except Exception as exc:
                    failed += 1
                    errors.append({
                        "row": idx + 1,
                        "msisdn": sim_in.msisdn,
                        "error": str(exc),
                    })

        await self.db.commit()

        return {
            "total_records": len(sims_in),
            "successful": successful,
            "failed": failed,
            "errors": errors if errors else None,
        }

    async def get_sim_by_id(self, sim_id: int) -> RecycledSIM | None:
        return await self.repository.get_by_id(sim_id)

    async def get_sim_by_msisdn(self, msisdn: str) -> RecycledSIM | None:
        msisdn = NigerianValidators.normalize_msisdn(msisdn)
        stmt = select(RecycledSIM).where(RecycledSIM.msisdn == msisdn)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_sims(
        self, skip: int = 0, limit: int = 50, filters: dict[str, Any] = None
    ) -> list[RecycledSIM]:
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)

    async def update_sim(self, sim_id: int, sim_in: RecycledSIMUpdate) -> RecycledSIM:
        sim = await self.get_sim_by_id(sim_id)
        if not sim:
            raise ResourceNotFoundError("RecycledSIM", sim_id)

        update_data = sim_in.model_dump(exclude_unset=True)
        updated_sim = await self.repository.update(sim_id, update_data)
        await self.db.commit()
        return updated_sim

    async def update_cleanup_status(
        self, sim_id: int, status: CleanupStatus
    ) -> RecycledSIM:
        sim = await self.get_sim_by_id(sim_id)
        if not sim:
            raise ResourceNotFoundError("RecycledSIM", sim_id)

        updated_sim = await self.repository.update(
            sim_id, {"cleanup_status": status}
        )
        await self.db.commit()
        return updated_sim

    async def count_sims(self, filters: dict[str, Any] = None) -> int:
        return await self.repository.count(filters=filters)

    async def get_sims_by_cleanup_status(
        self, status: CleanupStatus, skip: int = 0, limit: int = 50
    ) -> list[RecycledSIM]:
        return await self.get_all_sims(
            skip=skip, limit=limit, filters={"cleanup_status": status}
        )
