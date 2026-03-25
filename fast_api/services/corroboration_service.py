from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fast_api.models.nin_linkage import NINLinkage
from fast_api.models.bvn_linkage import BVNLinkage
from fast_api.models.recycled_sim import RecycledSIM
from fast_api.validators.nigerian import NigerianValidators

logger = logging.getLogger(__name__)


class CorroborationSource:
    def __init__(self, name: str, data: dict[str, Any] | None, available: bool):
        self.name = name
        self.data = data
        self.available = available


class IdentityMapping:
    def __init__(self, msisdn: str):
        self.msisdn = msisdn
        self.sources: list[CorroborationSource] = []
        self.nin: str | None = None
        self.bvn: str | None = None
        self.operator_code: str | None = None
        self.is_recycled: bool = False
        self.nin_active: bool = False
        self.bvn_active: bool = False
        self.confidence_score: float = 0.0
        self.conflicts: list[dict[str, Any]] = []
        self.last_verified: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "msisdn": self.msisdn,
            "nin": self.nin,
            "bvn": self.bvn,
            "operator_code": self.operator_code,
            "is_recycled": self.is_recycled,
            "nin_linkage_active": self.nin_active,
            "bvn_linkage_active": self.bvn_active,
            "confidence_score": round(self.confidence_score, 2),
            "conflicts": self.conflicts if self.conflicts else None,
            "sources_consulted": [
                {"name": s.name, "available": s.available} for s in self.sources
            ],
            "last_verified": self.last_verified.isoformat() if self.last_verified else None,
            "assessed_at": datetime.now(timezone.utc).isoformat(),
        }


class CorroborationService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_identity_mapping(self, msisdn: str) -> IdentityMapping:
        msisdn = NigerianValidators.normalize_msisdn(msisdn)
        mapping = IdentityMapping(msisdn)

        await self._load_local_sim_data(mapping)
        await self._load_local_nin_data(mapping)
        await self._load_local_bvn_data(mapping)
        self._compute_confidence(mapping)

        return mapping

    async def get_batch_mappings(
        self, msisdns: list[str]
    ) -> list[IdentityMapping]:
        results = []
        for msisdn in msisdns:
            mapping = await self.get_identity_mapping(msisdn)
            results.append(mapping)
        return results

    async def corroborate_with_external(
        self, msisdn: str, nimc_adapter=None, nibss_adapter=None, telecom_adapter=None
    ) -> IdentityMapping:
        msisdn = NigerianValidators.normalize_msisdn(msisdn)
        mapping = await self.get_identity_mapping(msisdn)

        if nimc_adapter:
            await self._corroborate_nimc(mapping, nimc_adapter)
        if nibss_adapter:
            await self._corroborate_nibss(mapping, nibss_adapter)
        if telecom_adapter:
            await self._corroborate_telecom(mapping, telecom_adapter)

        self._compute_confidence(mapping)
        return mapping

    async def _load_local_sim_data(self, mapping: IdentityMapping) -> None:
        stmt = select(RecycledSIM).where(RecycledSIM.msisdn == mapping.msisdn)
        result = await self.db.execute(stmt)
        sim = result.scalar_one_or_none()

        source = CorroborationSource(
            name="reconix_sims",
            data=None,
            available=sim is not None,
        )

        if sim:
            mapping.is_recycled = True
            mapping.operator_code = sim.operator_code
            source.data = {
                "sim_serial": sim.sim_serial,
                "operator_code": sim.operator_code,
                "cleanup_status": sim.cleanup_status,
                "date_recycled": sim.date_recycled.isoformat() if sim.date_recycled else None,
            }

        mapping.sources.append(source)

    async def _load_local_nin_data(self, mapping: IdentityMapping) -> None:
        stmt = select(NINLinkage).where(
            NINLinkage.msisdn == mapping.msisdn,
            NINLinkage.is_active == True,
        )
        result = await self.db.execute(stmt)
        linkage = result.scalar_one_or_none()

        source = CorroborationSource(
            name="reconix_nin",
            data=None,
            available=linkage is not None,
        )

        if linkage:
            mapping.nin = linkage.nin
            mapping.nin_active = True
            mapping.last_verified = linkage.verified_at
            source.data = {
                "nin": linkage.nin,
                "source": linkage.source,
                "linked_date": linkage.linked_date.isoformat() if linkage.linked_date else None,
                "verified_at": linkage.verified_at.isoformat() if linkage.verified_at else None,
            }

        mapping.sources.append(source)

    async def _load_local_bvn_data(self, mapping: IdentityMapping) -> None:
        stmt = select(BVNLinkage).where(
            BVNLinkage.msisdn == mapping.msisdn,
            BVNLinkage.is_active == True,
        )
        result = await self.db.execute(stmt)
        linkage = result.scalar_one_or_none()

        source = CorroborationSource(
            name="reconix_bvn",
            data=None,
            available=linkage is not None,
        )

        if linkage:
            mapping.bvn = linkage.bvn
            mapping.bvn_active = True
            source.data = {
                "bvn": linkage.bvn,
                "bank_code": linkage.bank_code,
                "source": linkage.source,
                "linked_date": linkage.linked_date.isoformat() if linkage.linked_date else None,
                "verified_at": linkage.verified_at.isoformat() if linkage.verified_at else None,
            }

        mapping.sources.append(source)

    async def _corroborate_nimc(self, mapping: IdentityMapping, adapter) -> None:
        try:
            result = await adapter.get_nin_for_msisdn(mapping.msisdn)
            external_nin = result.get("nin")

            source = CorroborationSource(
                name="nimc_api",
                data=result,
                available=True,
            )
            mapping.sources.append(source)

            if external_nin and mapping.nin and external_nin != mapping.nin:
                mapping.conflicts.append({
                    "field": "nin",
                    "local_value": mapping.nin,
                    "external_value": external_nin,
                    "external_source": "nimc_api",
                    "resolution": "requires_manual_review",
                })
            elif external_nin and not mapping.nin:
                mapping.nin = external_nin
                mapping.nin_active = True

        except ConnectionError:
            mapping.sources.append(
                CorroborationSource(name="nimc_api", data=None, available=False)
            )

    async def _corroborate_nibss(self, mapping: IdentityMapping, adapter) -> None:
        try:
            result = await adapter.get_bvn_for_msisdn(mapping.msisdn)
            external_bvn = result.get("bvn")

            source = CorroborationSource(
                name="nibss_api",
                data=result,
                available=True,
            )
            mapping.sources.append(source)

            if external_bvn and mapping.bvn and external_bvn != mapping.bvn:
                mapping.conflicts.append({
                    "field": "bvn",
                    "local_value": mapping.bvn,
                    "external_value": external_bvn,
                    "external_source": "nibss_api",
                    "resolution": "requires_manual_review",
                })
            elif external_bvn and not mapping.bvn:
                mapping.bvn = external_bvn
                mapping.bvn_active = True

        except ConnectionError:
            mapping.sources.append(
                CorroborationSource(name="nibss_api", data=None, available=False)
            )

    async def _corroborate_telecom(self, mapping: IdentityMapping, adapter) -> None:
        try:
            result = await adapter.get_sim_status(mapping.msisdn)
            source = CorroborationSource(
                name=f"telecom_{adapter.operator_code}",
                data=result,
                available=True,
            )
            mapping.sources.append(source)

            external_recycled = result.get("is_recycled", False)
            if external_recycled != mapping.is_recycled:
                mapping.conflicts.append({
                    "field": "is_recycled",
                    "local_value": mapping.is_recycled,
                    "external_value": external_recycled,
                    "external_source": f"telecom_{adapter.operator_code}",
                    "resolution": "requires_manual_review",
                })

        except ConnectionError:
            mapping.sources.append(
                CorroborationSource(
                    name=f"telecom_{getattr(adapter, 'operator_code', 'unknown')}",
                    data=None,
                    available=False,
                )
            )

    def _compute_confidence(self, mapping: IdentityMapping) -> None:
        total_sources = len(mapping.sources)
        available_sources = sum(1 for s in mapping.sources if s.available)
        conflict_count = len(mapping.conflicts)

        if total_sources == 0:
            mapping.confidence_score = 0.0
            return

        source_ratio = available_sources / max(total_sources, 1)

        data_completeness = 0.0
        checks = [
            mapping.nin is not None,
            mapping.bvn is not None,
            mapping.operator_code is not None,
            mapping.is_recycled is not None,
        ]
        data_completeness = sum(1 for c in checks if c) / len(checks)

        conflict_penalty = min(conflict_count * 0.25, 0.5)

        mapping.confidence_score = max(
            0.0,
            min(1.0, (source_ratio * 0.4 + data_completeness * 0.6) - conflict_penalty),
        )
