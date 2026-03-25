from __future__ import annotations

import json
import hashlib
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

_redis_available = False
try:
    import redis.asyncio as aioredis
    _redis_available = True
except ImportError:
    pass

_client: Any = None


class CacheService:

    def __init__(self, redis_url: str = "", prefix: str = "reconix"):
        self.prefix = prefix
        self._client = None
        self._redis_url = redis_url
        self._fallback: dict[str, tuple[Any, float]] = {}

    async def connect(self) -> bool:
        if not _redis_available:
            logger.warning("redis package not installed — using in-memory fallback")
            return False

        if not self._redis_url:
            logger.info("REDIS_URL not configured — using in-memory fallback")
            return False

        try:
            self._client = aioredis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=20,
            )
            await self._client.ping()
            logger.info("Redis connected")
            return True
        except Exception as e:
            logger.warning(f"Redis connection failed, using fallback: {e}")
            self._client = None
            return False

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Any | None:
        full_key = self._key(key)

        if self._client:
            try:
                value = await self._client.get(full_key)
                if value is not None:
                    return json.loads(value)
                return None
            except Exception:
                logger.debug(f"Redis get failed for key={key}")

        entry = self._fallback.get(full_key)
        if entry:
            value, expires_at = entry
            if expires_at == 0 or time.monotonic() < expires_at:
                return value
            del self._fallback[full_key]
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        full_key = self._key(key)
        serialized = json.dumps(value, default=str)

        if self._client:
            try:
                await self._client.set(full_key, serialized, ex=ttl_seconds)
                return True
            except Exception:
                logger.debug(f"Redis set failed for key={key}")

        expires_at = time.monotonic() + ttl_seconds if ttl_seconds > 0 else 0
        self._fallback[full_key] = (value, expires_at)
        return True

    async def delete(self, key: str) -> bool:
        full_key = self._key(key)

        if self._client:
            try:
                await self._client.delete(full_key)
                return True
            except Exception:
                logger.debug(f"Redis delete failed for key={key}")

        self._fallback.pop(full_key, None)
        return True

    async def invalidate_pattern(self, pattern: str) -> int:
        full_pattern = self._key(pattern)
        count = 0

        if self._client:
            try:
                cursor = 0
                while True:
                    cursor, keys = await self._client.scan(
                        cursor=cursor, match=full_pattern, count=100
                    )
                    if keys:
                        await self._client.delete(*keys)
                        count += len(keys)
                    if cursor == 0:
                        break
                return count
            except Exception:
                logger.debug(f"Redis invalidate failed for pattern={pattern}")

        prefix = full_pattern.rstrip("*")
        to_delete = [k for k in self._fallback if k.startswith(prefix)]
        for k in to_delete:
            del self._fallback[k]
        return len(to_delete)

    async def add_to_blacklist(self, token_jti: str, ttl_seconds: int) -> bool:
        return await self.set(f"blacklist:{token_jti}", True, ttl_seconds)

    async def is_blacklisted(self, token_jti: str) -> bool:
        result = await self.get(f"blacklist:{token_jti}")
        return result is True

    @staticmethod
    def cache_key(*parts: str) -> str:
        raw = ":".join(parts)
        return hashlib.sha256(raw.encode()).hexdigest()[:32]


_cache_instance: CacheService | None = None


def get_cache() -> CacheService:
    global _cache_instance
    if _cache_instance is None:
        from fast_api.config import get_settings
        settings = get_settings()
        redis_url = getattr(settings, "REDIS_URL", "")
        _cache_instance = CacheService(redis_url=redis_url)
    return _cache_instance


def reset_cache() -> None:
    global _cache_instance
    _cache_instance = None
