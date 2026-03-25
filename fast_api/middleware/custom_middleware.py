from __future__ import annotations

import logging
import time
import hashlib
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

CORS_SAFE_HEADERS = frozenset({
    "authorization", "content-type", "x-request-id", "x-api-key",
    "idempotency-key", "accept", "accept-language", "content-language",
})


class CustomSecurityMiddleware(BaseHTTPMiddleware):

    def __init__(
        self,
        app,
        enforce_content_type: bool = True,
        log_slow_requests_ms: float = 5000,
        block_trace_method: bool = True,
        max_header_size: int = 8192,
        max_url_length: int = 2048,
    ):
        super().__init__(app)
        self.enforce_content_type = enforce_content_type
        self.log_slow_requests_ms = log_slow_requests_ms
        self.block_trace_method = block_trace_method
        self.max_header_size = max_header_size
        self.max_url_length = max_url_length

    async def dispatch(self, request: Request, call_next) -> Response:
        if self.block_trace_method and request.method in ("TRACE", "TRACK"):
            return JSONResponse(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                content={
                    "code": "METHOD_NOT_ALLOWED",
                    "message": "TRACE/TRACK methods are not permitted",
                    "details": {},
                },
            )

        url_length = len(str(request.url))
        if url_length > self.max_url_length:
            return JSONResponse(
                status_code=status.HTTP_414_REQUEST_URI_TOO_LONG,
                content={
                    "code": "URI_TOO_LONG",
                    "message": f"URL exceeds maximum length of {self.max_url_length} characters",
                    "details": {},
                },
            )

        total_header_size = sum(
            len(k) + len(v) for k, v in request.headers.items()
        )
        if total_header_size > self.max_header_size:
            return JSONResponse(
                status_code=status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE,
                content={
                    "code": "HEADERS_TOO_LARGE",
                    "message": "Request headers exceed size limit",
                    "details": {},
                },
            )

        if (
            self.enforce_content_type
            and request.method not in SAFE_METHODS
            and request.headers.get("content-length", "0") != "0"
        ):
            content_type = request.headers.get("content-type", "")
            if content_type and "application/json" not in content_type and "multipart/form-data" not in content_type:
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={
                        "code": "UNSUPPORTED_MEDIA_TYPE",
                        "message": "Content-Type must be application/json or multipart/form-data",
                        "details": {},
                    },
                )

        host = request.headers.get("host", "")
        if not host:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "code": "INVALID_REQUEST",
                    "message": "Host header is required",
                    "details": {},
                },
            )

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000

        if duration_ms > self.log_slow_requests_ms:
            logger.warning(
                "slow_request",
                extra={
                    "extra_data": {
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": round(duration_ms, 2),
                        "ip": request.client.host if request.client else "unknown",
                    }
                },
            )

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"

        return response
