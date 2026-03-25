from __future__ import annotations

import re
import json
import logging
from urllib.parse import unquote
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

DANGEROUS_PATTERNS = [
    re.compile(r"\b(DROP|DELETE|INSERT|UPDATE|UNION|SELECT)\b", re.IGNORECASE),
    re.compile(r"\b(EXEC|EXECUTE)\b\s", re.IGNORECASE),
    re.compile(r"\b(GROUP_CONCAT|STRING_AGG|LOAD_FILE|INTO\s+OUTFILE)\b", re.IGNORECASE),
    re.compile(r"/\*.*?\*/", re.IGNORECASE),
    re.compile(r"<script", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"\bon\w+\s*=", re.IGNORECASE),
    re.compile(r";\s*(rm|cat|ls|wget|curl|bash|sh|nc|ncat|python|perl|ruby|php)\b", re.IGNORECASE),
    re.compile(r"\$\(", re.IGNORECASE),
    re.compile(r"`[^`]*`"),
    re.compile(r"\.\./"),
    re.compile(r"(\%27)|(\')|(\-\-)|(\%23)|(#)", re.IGNORECASE),
    re.compile(r"\x00"),
]

BODY_CHECK_METHODS = frozenset({"POST", "PUT", "PATCH"})
EXEMPT_PATHS = frozenset({"/health", "/metrics"})
MAX_BODY_SCAN_BYTES = 65536


def _extract_string_values(obj, depth: int = 0) -> list[str]:
    if depth > 5:
        return []
    values: list[str] = []
    if isinstance(obj, str):
        values.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            values.extend(_extract_string_values(v, depth + 1))
    elif isinstance(obj, list):
        for item in obj:
            values.extend(_extract_string_values(item, depth + 1))
    return values


class InputSanitizationMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        query_string = unquote(request.url.query or "")
        if self._check_patterns(query_string):
            return self._blocked_response(request, "query string")

        if request.method in BODY_CHECK_METHODS:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.body()
                    if body and len(body) <= MAX_BODY_SCAN_BYTES:
                        parsed = json.loads(body)
                        string_values = _extract_string_values(parsed)
                        for value in string_values:
                            if self._check_patterns(value):
                                return self._blocked_response(request, "request body")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

        return await call_next(request)

    @staticmethod
    def _check_patterns(text: str) -> bool:
        for pattern in DANGEROUS_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @staticmethod
    def _blocked_response(request: Request, source: str) -> JSONResponse:
        logger.warning(
            "blocked_dangerous_input",
            extra={
                "extra_data": {
                    "source": source,
                    "path": request.url.path,
                    "method": request.method,
                    "ip": request.client.host if request.client else "unknown",
                }
            },
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "code": "INVALID_INPUT",
                "message": "Request contains prohibited patterns",
                "details": {},
            },
        )
