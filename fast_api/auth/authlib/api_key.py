from __future__ import annotations

from datetime import datetime, timezone
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fast_api.auth.authlib.password import PasswordManager
from fast_api.exceptions import AuthenticationError
from fast_api.db import get_db
from fast_api.models.api_key import APIKey
from fast_api.models.user import User


async def verify_api_key(
    x_api_key: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not x_api_key:
        raise AuthenticationError("API key is required")

    stmt = (
        select(APIKey)
        .where(APIKey.is_active == True)
        .where(APIKey.expires_at > datetime.now(timezone.utc))
    )
    result = await db.execute(stmt)
    api_keys = result.scalars().all()

    for api_key in api_keys:
        if PasswordManager.verify_api_key(x_api_key, api_key.key_hash):
            user_stmt = select(User).where(User.id == api_key.user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            if user and user.is_active:
                return user

    raise AuthenticationError("Invalid or expired API key")
