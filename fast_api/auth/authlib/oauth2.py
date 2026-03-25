from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fast_api.auth.authlib.jwt_handler import JWTHandler
from fast_api.exceptions import AuthenticationError, AuthorizationError
from fast_api.db import get_db
from fast_api.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = JWTHandler.verify_token(token, expected_type="access")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "AUTHENTICATION_ERROR",
                    "message": "Invalid token payload",
                    "details": {},
                },
            )
    except HTTPException:
        raise
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTHENTICATION_ERROR",
                "message": "Could not validate credentials",
                "details": {},
            },
        )

    try:
        parsed_user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTHENTICATION_ERROR",
                "message": "Invalid token payload",
                "details": {},
            },
        )

    stmt = select(User).where(User.id == parsed_user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationError("User not found")

    if not user.is_active:
        raise AuthenticationError("User account is inactive")

    db.expunge(user)
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise AuthorizationError("Admin access required", required_role="admin")
    return current_user
