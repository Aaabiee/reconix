from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        forwarded_proto = request.headers.get("x-forwarded-proto", "")
        if forwarded_proto == "http":
            url = request.url.replace(scheme="https")
            return Response(status_code=301, headers={"Location": str(url)})

        return await call_next(request)
