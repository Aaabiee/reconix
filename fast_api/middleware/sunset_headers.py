from __future__ import annotations

import logging
from datetime import datetime, timezone
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

DEPRECATED_ENDPOINTS: dict[str, dict] = {}


class SunsetHeadersMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, deprecated_endpoints: dict[str, dict] | None = None):
        super().__init__(app)
        self.deprecated_endpoints = deprecated_endpoints or DEPRECATED_ENDPOINTS

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        path = request.url.path
        for pattern, info in self.deprecated_endpoints.items():
            if path.startswith(pattern):
                sunset_date = info.get("sunset")
                replacement = info.get("replacement", "")
                deprecation_date = info.get("deprecated_since", "")

                if sunset_date:
                    response.headers["Sunset"] = sunset_date
                if deprecation_date:
                    response.headers["Deprecation"] = deprecation_date
                if replacement:
                    response.headers["Link"] = f'<{replacement}>; rel="successor-version"'

                now = datetime.now(timezone.utc)
                try:
                    sunset_dt = datetime.fromisoformat(sunset_date.replace("Z", "+00:00"))
                    if now >= sunset_dt:
                        logger.warning(
                            "deprecated_endpoint_past_sunset",
                            extra={
                                "extra_data": {
                                    "path": path,
                                    "sunset": sunset_date,
                                    "replacement": replacement,
                                }
                            },
                        )
                except (ValueError, TypeError):
                    pass

                break

        response.headers["API-Version"] = "v1"

        return response
