from __future__ import annotations

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

_sentry_available = False
try:
    import sentry_sdk
    _sentry_available = True
except ImportError:
    pass


def init_sentry(dsn: str, environment: str, release: str = "1.0.0") -> bool:
    if not _sentry_available:
        logger.warning("sentry_sdk not installed — error tracking disabled")
        return False

    if not dsn:
        logger.info("SENTRY_DSN not configured — error tracking disabled")
        return False

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=f"reconix@{release}",
        traces_sample_rate=0.1 if environment == "production" else 1.0,
        profiles_sample_rate=0.1 if environment == "production" else 0.0,
        send_default_pii=False,
        before_send=_scrub_event,
        attach_stacktrace=True,
        max_breadcrumbs=50,
    )
    logger.info(f"Sentry initialized [env={environment}]")
    return True


PII_KEYS = frozenset({
    "password", "hashed_password", "token", "access_token",
    "refresh_token", "api_key", "secret", "authorization",
    "cookie", "nin", "bvn", "msisdn", "imsi",
})


def _scrub_event(event, hint):
    if "request" in event:
        req = event["request"]
        if "headers" in req:
            req["headers"] = {
                k: "[REDACTED]" if k.lower() in PII_KEYS else v
                for k, v in req["headers"].items()
            }
        if "data" in req and isinstance(req["data"], dict):
            req["data"] = _scrub_dict(req["data"])
        if "cookies" in req:
            req["cookies"] = "[REDACTED]"

    return event


def _scrub_dict(data: dict, depth: int = 0) -> dict:
    if depth > 5:
        return {"_truncated": True}
    result = {}
    for key, value in data.items():
        if key.lower() in PII_KEYS:
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = _scrub_dict(value, depth + 1)
        else:
            result[key] = value
    return result


class SentryMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        if not _sentry_available:
            return await call_next(request)

        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("http.method", request.method)
            scope.set_tag("http.path", request.url.path)

            trace_id = getattr(request.state, "trace_id", None)
            if trace_id:
                scope.set_tag("trace_id", trace_id)

            request_id = request.headers.get("X-Request-ID", "")
            if request_id:
                scope.set_tag("request_id", request_id)

        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            if _sentry_available:
                sentry_sdk.capture_exception(exc)
            raise
