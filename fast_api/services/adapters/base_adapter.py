from __future__ import annotations

import ipaddress
import logging
from typing import Any
from urllib.parse import urlparse
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

BLOCKED_HOSTS = frozenset({
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
    "metadata.google.internal", "169.254.169.254",
})

BLOCKED_SUFFIXES = (".internal", ".local", ".localhost")


def validate_outbound_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""

        if parsed.scheme not in ("https",):
            return False

        if hostname in BLOCKED_HOSTS:
            return False

        for suffix in BLOCKED_SUFFIXES:
            if hostname.endswith(suffix):
                return False

        try:
            addr = ipaddress.ip_address(hostname)
            if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
                return False
        except ValueError:
            pass

        return True
    except Exception:
        return False


class StakeholderAdapter:

    def __init__(
        self,
        name: str,
        base_url: str,
        auth_token: str = "",
        timeout: int = 30,
        rate_limit: int = 60,
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self._auth_token = auth_token
        self._timeout = timeout
        self._rate_limit = rate_limit
        self._request_count = 0
        self._window_start = datetime.now(timezone.utc)

    def _check_rate_limit(self) -> bool:
        now = datetime.now(timezone.utc)
        elapsed = (now - self._window_start).total_seconds()
        if elapsed >= 60:
            self._request_count = 0
            self._window_start = now
        return self._request_count < self._rate_limit

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "Reconix/1.0 (Identity Reconciliation Platform)",
        }
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        return headers

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"

        if not validate_outbound_url(url):
            raise ConnectionError(f"SSRF protection: blocked outbound request to {url}")

        if not self._check_rate_limit():
            raise ConnectionError(f"Rate limit exceeded for {self.name}")

        self._request_count += 1

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=False,
                verify=True,
            ) as client:
                response = await client.get(url, headers=self._build_headers(), params=params)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to {self.name}: {url}")
            raise ConnectionError(f"Timeout connecting to {self.name}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP {e.response.status_code} from {self.name}: {url}")
            raise ConnectionError(f"HTTP {e.response.status_code} from {self.name}")
        except Exception as e:
            logger.error(f"Connection error to {self.name}: {e}")
            raise ConnectionError(f"Failed to connect to {self.name}")

    async def health_check(self) -> dict[str, Any]:
        try:
            result = await self._get("/health")
            return {"stakeholder": self.name, "status": "reachable", "details": result}
        except ConnectionError as e:
            return {"stakeholder": self.name, "status": "unreachable", "error": str(e)}
