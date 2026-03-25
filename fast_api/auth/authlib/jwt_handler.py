from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from fast_api.config import get_settings
from fast_api.exceptions import AuthenticationError

settings = get_settings()


class JWTHandler:

    @staticmethod
    def create_access_token(
        data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                hours=settings.JWT_EXPIRATION_HOURS
            )
        to_encode.update({
            "exp": expire,
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_hex(16),
        })
        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    @staticmethod
    def create_refresh_token(data: dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRATION_DAYS
        )
        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_hex(16),
        })
        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    @staticmethod
    def verify_token(token: str, expected_type: str = "access") -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            token_type = payload.get("type", "access")
            if token_type != expected_type:
                raise AuthenticationError(f"Expected {expected_type} token, got {token_type}")
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
