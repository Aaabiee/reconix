from __future__ import annotations

import logging
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fast_api.config import get_settings
from fast_api.exceptions import ReconixException, AuthorizationError
from fast_api.exceptions.handlers import (
    to_http_exception,
    authorization_exception_handler,
    reconix_exception_handler,
    validation_exception_handler,
)
from fast_api.db import init_db, close_db, get_engine
from fast_api.api import api_router
from fast_api.middleware.security_headers import SecurityHeadersMiddleware
from fast_api.middleware.request_tracking import RequestIDMiddleware
from fast_api.middleware.input_guard import InputSanitizationMiddleware
from fast_api.middleware.size_limiter import RequestSizeLimitMiddleware
from fast_api.middleware.https_enforcer import HTTPSRedirectMiddleware
from fast_api.middleware.audit_logger import AuditLoggingMiddleware
from fast_api.middleware.rate_limiter import limiter
from fast_api.middleware.metrics import MetricsMiddleware, metrics_endpoint
from fast_api.middleware.custom_middleware import CustomSecurityMiddleware
from fast_api.middleware.tracing import TracingMiddleware
from fast_api.middleware.sunset_headers import SunsetHeadersMiddleware
from fast_api.middleware.sentry_integration import init_sentry, SentryMiddleware
from fast_api.logging_config import configure_logging

settings = get_settings()

configure_logging(
    log_level=settings.LOG_LEVEL,
    json_output=settings.ENABLE_JSON_LOGGING and not settings.is_development,
)
logger = logging.getLogger(__name__)

if settings.SENTRY_DSN:
    init_sentry(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        release=settings.SENTRY_RELEASE,
    )

shutdown_event = asyncio.Event()


DB_RETRY_ATTEMPTS = 5
DB_RETRY_DELAY_SECONDS = 2


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Reconix API [env={settings.ENVIRONMENT}]")

    for attempt in range(1, DB_RETRY_ATTEMPTS + 1):
        try:
            await init_db()
            logger.info("Database initialized successfully")
            break
        except Exception as e:
            if attempt == DB_RETRY_ATTEMPTS:
                logger.critical(f"Database initialization failed after {DB_RETRY_ATTEMPTS} attempts: {e}")
                raise
            delay = DB_RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
            logger.warning(f"Database connection attempt {attempt}/{DB_RETRY_ATTEMPTS} failed, retrying in {delay}s: {e}")
            await asyncio.sleep(delay)

    from fast_api.services.cache_service import get_cache
    cache = get_cache()
    await cache.connect()

    app.state.ready = True

    yield

    app.state.ready = False
    await cache.close()

    logger.info("Shutting down Reconix API")
    shutdown_event.set()
    await close_db()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Reconix API",
    description="National-scale identity reconciliation platform for Nigeria",
    version="1.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
    lifespan=lifespan,
)

app.state.limiter = limiter

if settings.ENFORCE_HTTPS and settings.is_production:
    app.add_middleware(HTTPSRedirectMiddleware)

if settings.SENTRY_DSN:
    app.add_middleware(SentryMiddleware)

if settings.ENABLE_TRACING:
    app.add_middleware(TracingMiddleware)

app.add_middleware(SunsetHeadersMiddleware)

if settings.ENABLE_IDEMPOTENCY:
    from fast_api.middleware.idempotency import IdempotencyMiddleware
    app.add_middleware(IdempotencyMiddleware)

if settings.ENABLE_METRICS:
    app.add_middleware(MetricsMiddleware)

app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(CustomSecurityMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(InputSanitizationMiddleware)
app.add_middleware(RequestSizeLimitMiddleware, max_size_mb=settings.MAX_REQUEST_SIZE_MB)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-API-Key"],
)

app.add_exception_handler(AuthorizationError, authorization_exception_handler)
app.add_exception_handler(ReconixException, reconix_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


@app.get("/health")
async def health_check():
    from sqlalchemy import text

    db_healthy = False
    pool_info = {}
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_healthy = True

        pool = engine.pool
        try:
            pool_info = {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            }
        except AttributeError:
            pool_info = {}
    except Exception:
        db_healthy = False

    http_status = 200 if db_healthy else 503

    return JSONResponse(
        status_code=http_status,
        content={
            "status": "healthy" if db_healthy else "degraded",
            "version": "1.0.0",
            "database": "connected" if db_healthy else "unreachable",
            "pool": pool_info,
        },
    )


@app.get("/health/live")
async def liveness():
    return JSONResponse(status_code=200, content={"status": "alive"})


@app.get("/health/ready")
async def readiness():
    ready = getattr(app.state, "ready", False)
    if not ready:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return JSONResponse(status_code=200, content={"status": "ready"})


if settings.ENABLE_METRICS:
    @app.get("/metrics")
    async def get_metrics(request: Request):
        if settings.is_production:
            client_ip = request.client.host if request.client else ""
            allowed = settings.ALLOWED_HOSTS + ["127.0.0.1", "::1", "10.0.0.0/8"]
            if client_ip and not any(client_ip.startswith(h.split("/")[0]) for h in allowed):
                return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        return metrics_endpoint()


app.include_router(api_router)

if settings.ENABLE_WEBSOCKET:
    from fast_api.routes.ws import router as ws_router
    app.include_router(ws_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "fast_api.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "443")),
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )
