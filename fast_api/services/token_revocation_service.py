from __future__ import annotations

import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from fast_api.models.revoked_token import RevokedToken

logger = logging.getLogger(__name__)


class TokenRevocationService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def revoke_token(
        self, jti: str, expires_at: datetime, user_id: str | None = None
    ) -> None:
        existing = await self.db.execute(
            select(RevokedToken).where(RevokedToken.jti == jti)
        )
        if existing.scalar_one_or_none():
            return

        token = RevokedToken(
            jti=jti,
            user_id=user_id,
            expires_at=expires_at,
        )
        self.db.add(token)
        await self.db.flush()

    async def is_revoked(self, jti: str) -> bool:
        result = await self.db.execute(
            select(RevokedToken).where(RevokedToken.jti == jti)
        )
        return result.scalar_one_or_none() is not None

    async def revoke_all_for_user(
        self, user_id: str, expires_at: datetime
    ) -> None:
        token = RevokedToken(
            jti=f"all_{user_id}_{int(datetime.now(timezone.utc).timestamp())}",
            user_id=user_id,
            expires_at=expires_at,
        )
        self.db.add(token)
        await self.db.flush()

    async def cleanup_expired(self) -> int:
        stmt = delete(RevokedToken).where(
            RevokedToken.expires_at < datetime.now(timezone.utc)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount or 0
