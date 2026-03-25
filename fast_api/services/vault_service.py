from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_hvac_available = False
try:
    import hvac
    _hvac_available = True
except ImportError:
    pass


class VaultService:

    def __init__(
        self,
        vault_url: str = "",
        vault_token: str = "",
        mount_point: str = "secret",
    ):
        self._client = None
        self._vault_url = vault_url
        self._vault_token = vault_token
        self._mount_point = mount_point
        self._connected = False

    def connect(self) -> bool:
        if not _hvac_available:
            logger.warning("hvac package not installed — Vault integration disabled")
            return False

        if not self._vault_url or not self._vault_token:
            logger.info("Vault not configured — using environment variables for secrets")
            return False

        try:
            self._client = hvac.Client(
                url=self._vault_url,
                token=self._vault_token,
                timeout=10,
            )
            if self._client.is_authenticated():
                self._connected = True
                logger.info("HashiCorp Vault connected")
                return True
            logger.warning("Vault authentication failed")
            return False
        except Exception as e:
            logger.warning(f"Vault connection failed: {e}")
            return False

    def get_secret(self, path: str, key: str | None = None) -> dict[str, Any] | str | None:
        if self._client and self._connected:
            try:
                response = self._client.secrets.kv.v2.read_secret_version(
                    path=path,
                    mount_point=self._mount_point,
                )
                data = response["data"]["data"]
                if key:
                    return data.get(key)
                return data
            except Exception as e:
                logger.error(f"Vault secret read failed for path={path}: {e}")

        return self._env_fallback(path, key)

    def _env_fallback(self, path: str, key: str | None = None) -> str | None:
        env_key = path.upper().replace("/", "_").replace("-", "_")
        if key:
            env_key = f"{env_key}_{key.upper()}"
        return os.environ.get(env_key)

    def get_database_url(self) -> str | None:
        result = self.get_secret("reconix/database", "url")
        if isinstance(result, str):
            return result
        return os.environ.get("DATABASE_URL")

    def get_jwt_secret(self) -> str | None:
        result = self.get_secret("reconix/auth", "jwt_secret_key")
        if isinstance(result, str):
            return result
        return os.environ.get("JWT_SECRET_KEY")

    def get_encryption_key(self) -> str | None:
        result = self.get_secret("reconix/crypto", "field_encryption_key")
        if isinstance(result, str):
            return result
        return os.environ.get("FIELD_ENCRYPTION_KEY")

    @property
    def is_connected(self) -> bool:
        return self._connected


_vault_instance: VaultService | None = None


def get_vault() -> VaultService:
    global _vault_instance
    if _vault_instance is None:
        from fast_api.config import get_settings
        settings = get_settings()
        vault_url = getattr(settings, "VAULT_URL", "")
        vault_token = getattr(settings, "VAULT_TOKEN", "")
        _vault_instance = VaultService(
            vault_url=vault_url,
            vault_token=vault_token,
        )
    return _vault_instance


def reset_vault() -> None:
    global _vault_instance
    _vault_instance = None
