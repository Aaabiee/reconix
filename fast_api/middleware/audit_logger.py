from __future__ import annotations

import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class AuditLoggingMiddleware(BaseHTTPMiddleware):

    SENSITIVE_PATHS = ["/auth/login", "/auth/refresh"]
    SENSITIVE_FIELDS = ["password", "token", "api_key", "secret", "refresh_token"]

    async def dispatch(self, request: Request, call_next) -> Response:
        method = request.method
        path = request.url.path
        remote_addr = request.client.host if request.client else "unknown"
        request_id = getattr(request.state, "request_id", "unknown")
        start_time = time.monotonic()

        response = await call_next(request)

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)

        log_record = logger.makeRecord(
            logger.name, logging.INFO, "", 0,
            "http_request", (), None,
        )
        log_record.request_id = request_id
        log_record.extra_data = {
            "event": "http_request",
            "method": method,
            "path": path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "ip": remote_addr,
        }
        logger.handle(log_record)

        if response.status_code >= 400:
            warn_record = logger.makeRecord(
                logger.name, logging.WARNING, "", 0,
                "http_error", (), None,
            )
            warn_record.request_id = request_id
            warn_record.extra_data = {
                "event": "http_error",
                "method": method,
                "path": path,
                "status": response.status_code,
                "ip": remote_addr,
            }
            logger.handle(warn_record)

        return response

    def _redact_sensitive_fields(self, data: dict) -> None:
        for key in list(data.keys()):
            if key.lower() in self.SENSITIVE_FIELDS:
                data[key] = "[REDACTED]"
            elif isinstance(data[key], dict):
                self._redact_sensitive_fields(data[key])
