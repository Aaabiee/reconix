from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fast_api.models.stakeholder import Stakeholder, StakeholderType, StakeholderStatus
from fast_api.models.recycled_sim import RecycledSIM
from fast_api.services.linkage_service import NINLinkageService, BVNLinkageService
from fast_api.services.recycled_sim_service import RecycledSIMService
from fast_api.services.adapters.nimc_adapter import NIMCAdapter
from fast_api.services.adapters.nibss_adapter import NIBSSAdapter
from fast_api.services.adapters.telecom_adapter import TelecomAdapter
from fast_api.db import BaseRepository

logger = logging.getLogger(__name__)


class SyncOrchestrator:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.stakeholder_repo = BaseRepository(db, Stakeholder)

    async def sync_all(self) -> dict[str, Any]:
        results = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "stakeholders": [],
        }

        stmt = select(Stakeholder).where(
            Stakeholder.status == StakeholderStatus.ACTIVE
        )
        result = await self.db.execute(stmt)
        stakeholders = result.scalars().all()

        for stakeholder in stakeholders:
            try:
                sync_result = await self._sync_stakeholder(stakeholder)
                results["stakeholders"].append(sync_result)
            except Exception as e:
                logger.error(
                    f"Sync failed for {stakeholder.name}: {e}",
                    extra={"extra_data": {"stakeholder": stakeholder.code}},
                )
                results["stakeholders"].append({
                    "name": stakeholder.name,
                    "code": stakeholder.code,
                    "status": "failed",
                    "error": str(e),
                })

        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        return results

    async def sync_stakeholder_by_code(self, code: str) -> dict[str, Any]:
        stmt = select(Stakeholder).where(Stakeholder.code == code)
        result = await self.db.execute(stmt)
        stakeholder = result.scalar_one_or_none()

        if not stakeholder:
            return {"status": "not_found", "code": code}

        if stakeholder.status != StakeholderStatus.ACTIVE:
            return {"status": "inactive", "code": code}

        return await self._sync_stakeholder(stakeholder)

    async def _sync_stakeholder(self, stakeholder: Stakeholder) -> dict[str, Any]:
        sync_start = datetime.now(timezone.utc)
        records_synced = 0

        if stakeholder.stakeholder_type == StakeholderType.NIMC:
            records_synced = await self._sync_nimc(stakeholder)
        elif stakeholder.stakeholder_type == StakeholderType.NIBSS:
            records_synced = await self._sync_nibss(stakeholder)
        elif stakeholder.stakeholder_type == StakeholderType.TELECOM:
            records_synced = await self._sync_telecom(stakeholder)

        await self.stakeholder_repo.update(
            stakeholder.id,
            {
                "last_sync_at": sync_start,
                "last_sync_status": "success",
                "last_sync_records": records_synced,
            },
        )
        await self.db.commit()

        return {
            "name": stakeholder.name,
            "code": stakeholder.code,
            "type": stakeholder.stakeholder_type,
            "status": "success",
            "records_synced": records_synced,
            "synced_at": sync_start.isoformat(),
        }

    async def _sync_nimc(self, stakeholder: Stakeholder) -> int:
        adapter = NIMCAdapter(
            base_url=stakeholder.api_base_url,
            timeout=stakeholder.timeout_seconds,
        )

        pending_sims = await self._get_sims_needing_nin_check()
        if not pending_sims:
            return 0

        nin_service = NINLinkageService(self.db)
        synced = 0

        for sim in pending_sims:
            try:
                result = await adapter.get_nin_for_msisdn(sim.msisdn)
                nin = result.get("nin")
                if nin:
                    existing = await nin_service.get_active_linkage_for_msisdn(sim.msisdn)
                    if not existing:
                        await nin_service.create_linkage(
                            msisdn=sim.msisdn,
                            nin=nin,
                            source="nimc_api",
                        )
                        synced += 1
            except ConnectionError:
                logger.warning(f"NIMC lookup failed for {sim.msisdn}")

        return synced

    async def _sync_nibss(self, stakeholder: Stakeholder) -> int:
        adapter = NIBSSAdapter(
            base_url=stakeholder.api_base_url,
            timeout=stakeholder.timeout_seconds,
        )

        pending_sims = await self._get_sims_needing_bvn_check()
        if not pending_sims:
            return 0

        bvn_service = BVNLinkageService(self.db)
        synced = 0

        for sim in pending_sims:
            try:
                result = await adapter.get_bvn_for_msisdn(sim.msisdn)
                bvn = result.get("bvn")
                bank_code = result.get("bank_code")
                if bvn:
                    existing = await bvn_service.get_active_linkage_for_msisdn(sim.msisdn)
                    if not existing:
                        await bvn_service.create_linkage(
                            msisdn=sim.msisdn,
                            bvn=bvn,
                            bank_code=bank_code,
                            source="nibss_api",
                        )
                        synced += 1
            except ConnectionError:
                logger.warning(f"NIBSS lookup failed for {sim.msisdn}")

        return synced

    async def _sync_telecom(self, stakeholder: Stakeholder) -> int:
        adapter = TelecomAdapter(
            name=stakeholder.name,
            operator_code=stakeholder.code,
            base_url=stakeholder.api_base_url,
            timeout=stakeholder.timeout_seconds,
        )

        since = stakeholder.last_sync_at.isoformat() if stakeholder.last_sync_at else None

        try:
            sims_data = await adapter.get_recycled_sims(since=since)
        except ConnectionError:
            logger.warning(f"Telecom sync failed for {stakeholder.name}")
            return 0

        sim_service = RecycledSIMService(self.db)
        synced = 0

        for sim_data in sims_data:
            msisdn = sim_data.get("msisdn", "")
            if not msisdn:
                continue

            existing = await sim_service.get_sim_by_msisdn(msisdn)
            if not existing:
                try:
                    await sim_service.create_sim_from_dict({
                        "sim_serial": sim_data.get("sim_serial", ""),
                        "msisdn": msisdn,
                        "imsi": sim_data.get("imsi", ""),
                        "operator_code": stakeholder.code,
                        "date_recycled": sim_data.get("date_recycled", datetime.now(timezone.utc).isoformat()),
                    })
                    synced += 1
                except Exception:
                    logger.warning(f"Failed to create SIM record for {msisdn}")

        return synced

    async def _get_sims_needing_nin_check(self, limit: int = 100) -> list[RecycledSIM]:
        stmt = (
            select(RecycledSIM)
            .where(RecycledSIM.previous_nin_linked == True)
            .where(RecycledSIM.cleanup_status == "pending")
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _get_sims_needing_bvn_check(self, limit: int = 100) -> list[RecycledSIM]:
        stmt = (
            select(RecycledSIM)
            .where(RecycledSIM.previous_bvn_linked == True)
            .where(RecycledSIM.cleanup_status == "pending")
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
