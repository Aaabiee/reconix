from __future__ import annotations

import logging
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

EXCLUDED_PATHS = frozenset({"/health", "/metrics", "/favicon.ico"})


class TracingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if path in EXCLUDED_PATHS:
            return await call_next(request)

        trace_id = request.headers.get("X-Trace-ID", uuid.uuid4().hex)
        span_id = uuid.uuid4().hex[:16]
        parent_span_id = request.headers.get("X-Parent-Span-ID", "")

        request.state.trace_id = trace_id
        request.state.span_id = span_id

        start_time = time.monotonic()

        try:
            response = await call_next(request)
            duration_ms = (time.monotonic() - start_time) * 1000

            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Span-ID"] = span_id

            logger.info(
                "request_trace",
                extra={
                    "extra_data": {
                        "trace_id": trace_id,
                        "span_id": span_id,
                        "parent_span_id": parent_span_id,
                        "method": request.method,
                        "path": path,
                        "status_code": response.status_code,
                        "duration_ms": round(duration_ms, 2),
                        "client_ip": request.client.host if request.client else "unknown",
                        "user_agent": request.headers.get("User-Agent", ""),
                    }
                },
            )

            return response
        except Exception as exc:
            duration_ms = (time.monotonic() - start_time) * 1000
            logger.error(
                "request_trace_error",
                extra={
                    "extra_data": {
                        "trace_id": trace_id,
                        "span_id": span_id,
                        "method": request.method,
                        "path": path,
                        "duration_ms": round(duration_ms, 2),
                        "error": type(exc).__name__,
                    }
                },
            )
            raise
