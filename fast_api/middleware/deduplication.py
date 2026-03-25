from __future__ import annotations

import hashlib
import logging
import time
import threading
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)

DEDUP_WINDOW_SECONDS = 5
MAX_CACHE_SIZE = 10000


class DeduplicationCache:

    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> DeduplicationCache:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._data_lock = threading.Lock()
        self._cache: dict[str, float] = {}

    def is_duplicate(self, key: str) -> bool:
        now = time.monotonic()
        self._evict_expired(now)

        with self._data_lock:
            if key in self._cache:
                return True
            self._cache[key] = now
            return False

    def _evict_expired(self, now: float) -> None:
        with self._data_lock:
            expired = [
                k for k, ts in self._cache.items()
                if now - ts > DEDUP_WINDOW_SECONDS
            ]
            for k in expired:
                del self._cache[k]

            if len(self._cache) > MAX_CACHE_SIZE:
                oldest_keys = sorted(
                    self._cache, key=self._cache.get
                )[:len(self._cache) - MAX_CACHE_SIZE]
                for k in oldest_keys:
                    del self._cache[k]

    def reset(self) -> None:
        with self._data_lock:
            self._cache.clear()


class DeduplicationMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        if request.headers.get("Idempotency-Key"):
            return await call_next(request)

        body = b""
        try:
            body = await request.body()
        except Exception:
            return await call_next(request)

        auth_identity = request.headers.get("Authorization", "")
        if auth_identity:
            auth_identity = hashlib.sha256(auth_identity.encode()).hexdigest()[:16]

        fingerprint = hashlib.sha256(
            f"{request.method}:{request.url.path}:{auth_identity}:{body.hex()}".encode()
        ).hexdigest()

        cache = DeduplicationCache()
        if cache.is_duplicate(fingerprint):
            logger.info(f"dedup_rejected path={request.url.path}")
            return JSONResponse(
                status_code=409,
                content={
                    "code": "DUPLICATE_REQUEST",
                    "message": "Duplicate request detected within deduplication window",
                    "details": {},
                },
            )

        return await call_next(request)
