from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
from fast_api.auth.authlib.oauth2 import get_current_user
from fast_api.db import get_db
from fast_api.config import get_settings
from fast_api.auth.authlib.jwt_handler import JWTHandler
from fast_api.auth.authlib.password import PasswordManager
from fast_api.exceptions import AuthenticationError, AccountLockedError
from fast_api.exceptions.handlers import to_http_exception
from fast_api.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest
from fast_api.services.user_service import UserService
from fast_api.services.token_revocation_service import TokenRevocationService
from fast_api.models.user import User
from fast_api.middleware.rate_limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
@limiter.limit(f"{settings.AUTH_RATE_LIMIT_PER_MINUTE}/minute")
async def login(
    request: Request,
    login_request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_email(login_request.email)

        if not user:
            PasswordManager.verify_password("dummy", "$2b$12$" + "x" * 53)
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Invalid email or password")

        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise AccountLockedError(
                unlock_time=user.locked_until.isoformat()
            )

        if not PasswordManager.verify_password(
            login_request.password, user.hashed_password
        ):
            await user_service.increment_login_attempts(user.id)
            attempts = user.failed_login_attempts + 1

            if attempts >= settings.MAX_LOGIN_ATTEMPTS:
                await user_service.lock_user_account(
                    user.id, settings.ACCOUNT_LOCKOUT_MINUTES
                )

            raise AuthenticationError("Invalid email or password")

        await user_service.reset_login_attempts(user.id)

        await user_service.repository.update(
            user.id, {"last_login": datetime.now(timezone.utc)}
        )
        await db.commit()

        access_token = JWTHandler.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )
        refresh_token = JWTHandler.create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
        )

    except (AuthenticationError, AccountLockedError) as e:
        raise to_http_exception(e)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    token_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        payload = JWTHandler.verify_token(token_request.refresh_token, expected_type="refresh")

        old_jti = payload.get("jti")
        if old_jti:
            revocation_service = TokenRevocationService(db)
            if await revocation_service.is_revoked(old_jti):
                raise AuthenticationError("Token has been revoked")

            exp = payload.get("exp", 0)
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
            await revocation_service.revoke_token(
                jti=old_jti,
                expires_at=expires_at,
                user_id=payload.get("sub"),
            )
            await db.commit()

        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role", "")

        access_token = JWTHandler.create_access_token(
            data={"sub": user_id, "email": email, "role": role}
        )
        new_refresh_token = JWTHandler.create_refresh_token(
            data={"sub": user_id, "email": email, "role": role}
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
        )

    except AuthenticationError as e:
        raise to_http_exception(e)


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = JWTHandler.verify_token(token, expected_type="access")
            jti = payload.get("jti")
            if jti:
                revocation_service = TokenRevocationService(db)
                exp = payload.get("exp", 0)
                expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
                await revocation_service.revoke_token(
                    jti=jti,
                    expires_at=expires_at,
                    user_id=str(current_user.id),
                )
                await db.commit()
        except Exception:
            pass

    return {"message": "Logged out successfully"}
