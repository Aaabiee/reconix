from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
from sqlalchemy import select, delete
from fast_api.db import get_session_factory
from fast_api.models.idempotency_key import IdempotencyKey

logger = logging.getLogger(__name__)

IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_TTL_HOURS = 24


class IdempotencyMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        idem_key = request.headers.get(IDEMPOTENCY_HEADER)
        if not idem_key:
            return await call_next(request)

        if len(idem_key) > 255:
            return JSONResponse(
                status_code=422,
                content={
                    "code": "VALIDATION_ERROR",
                    "message": "Idempotency-Key must be 255 characters or fewer",
                    "details": {},
                },
            )

        request_user_id = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                import jwt as pyjwt
                from fast_api.config import get_settings
                settings = get_settings()
                payload = pyjwt.decode(
                    auth_header[7:],
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM],
                )
                request_user_id = payload.get("sub")
            except Exception:
                pass

        factory = get_session_factory()
        async with factory() as session:
            stmt = select(IdempotencyKey).where(IdempotencyKey.key == idem_key)
            if request_user_id:
                stmt = stmt.where(IdempotencyKey.user_id == request_user_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                if existing.expires_at < datetime.now(timezone.utc):
                    await session.delete(existing)
                    await session.commit()
                elif existing.response_body is not None:
                    logger.info(f"idempotency_replay key={idem_key} path={existing.path}")
                    try:
                        body = json.loads(existing.response_body)
                    except (json.JSONDecodeError, TypeError):
                        body = existing.response_body
                    return JSONResponse(
                        status_code=existing.status_code or 200,
                        content=body,
                        headers={"Idempotency-Key-Replayed": "true"},
                    )
                else:
                    return JSONResponse(
                        status_code=409,
                        content={
                            "code": "CONFLICT",
                            "message": "A request with this idempotency key is already being processed",
                            "details": {},
                        },
                    )

        factory = get_session_factory()
        async with factory() as session:
            new_record = IdempotencyKey(
                key=idem_key,
                method=request.method,
                path=request.url.path,
                user_id=request_user_id,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=IDEMPOTENCY_TTL_HOURS),
            )
            session.add(new_record)
            await session.commit()

        response = await call_next(request)

        body_bytes = b""
        async for chunk in response.body_iterator:
            if isinstance(chunk, str):
                body_bytes += chunk.encode("utf-8")
            else:
                body_bytes += chunk

        factory = get_session_factory()
        async with factory() as session:
            stmt = select(IdempotencyKey).where(IdempotencyKey.key == idem_key)
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
            if record:
                record.status_code = response.status_code
                record.response_body = body_bytes.decode("utf-8", errors="replace")
                await session.commit()

        return Response(
            content=body_bytes,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )


async def cleanup_expired_idempotency_keys() -> int:
    factory = get_session_factory()
    async with factory() as session:
        stmt = delete(IdempotencyKey).where(
            IdempotencyKey.expires_at < datetime.now(timezone.utc)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount or 0
