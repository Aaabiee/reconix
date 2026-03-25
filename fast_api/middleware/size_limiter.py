from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, max_size_mb: int = 10):
        super().__init__(app)
        self.max_size_bytes = max_size_mb * 1024 * 1024

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        try:
            if content_length and int(content_length) > self.max_size_bytes:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "code": "REQUEST_TOO_LARGE",
                        "message": f"Request body exceeds {self.max_size_bytes // (1024 * 1024)}MB limit",
                        "details": {},
                    },
                )
        except (ValueError, TypeError):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "code": "INVALID_REQUEST",
                    "message": "Invalid Content-Length header",
                    "details": {},
                },
            )

        return await call_next(request)
