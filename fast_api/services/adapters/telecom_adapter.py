from __future__ import annotations

import logging
from typing import Any
from fast_api.services.adapters.base_adapter import StakeholderAdapter

logger = logging.getLogger(__name__)


class TelecomAdapter(StakeholderAdapter):

    def __init__(
        self,
        name: str,
        operator_code: str,
        base_url: str,
        auth_token: str = "",
        timeout: int = 30,
    ):
        super().__init__(
            name=name,
            base_url=base_url,
            auth_token=auth_token,
            timeout=timeout,
        )
        self.operator_code = operator_code

    async def get_recycled_sims(
        self, since: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if since:
            params["since"] = since
        result = await self._get("/v1/sims/recycled", params=params)
        return result.get("sims", [])

    async def get_sim_status(self, msisdn: str) -> dict[str, Any]:
        return await self._get(
            "/v1/sims/status",
            params={"msisdn": msisdn},
        )

    async def verify_sim_owner(self, msisdn: str, imsi: str) -> dict[str, Any]:
        return await self._get(
            "/v1/sims/verify-owner",
            params={"msisdn": msisdn, "imsi": imsi},
        )
