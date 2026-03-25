from __future__ import annotations

import logging
from typing import Any
from fast_api.services.adapters.base_adapter import StakeholderAdapter

logger = logging.getLogger(__name__)


class NIBSSAdapter(StakeholderAdapter):

    def __init__(self, base_url: str, auth_token: str = "", timeout: int = 30):
        super().__init__(
            name="NIBSS",
            base_url=base_url,
            auth_token=auth_token,
            timeout=timeout,
        )

    async def verify_bvn_linkage(self, msisdn: str, bvn: str) -> dict[str, Any]:
        return await self._get(
            "/v1/bvn/verify",
            params={"msisdn": msisdn, "bvn": bvn},
        )

    async def get_bvn_for_msisdn(self, msisdn: str) -> dict[str, Any]:
        return await self._get(
            "/v1/bvn/lookup",
            params={"msisdn": msisdn},
        )

    async def batch_lookup_bvns(self, msisdns: list[str]) -> list[dict[str, Any]]:
        results = []
        for msisdn in msisdns:
            try:
                result = await self.get_bvn_for_msisdn(msisdn)
                results.append({"msisdn": msisdn, "status": "found", **result})
            except ConnectionError:
                results.append({"msisdn": msisdn, "status": "error"})
        return results
