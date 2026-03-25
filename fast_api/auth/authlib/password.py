from __future__ import annotations

import secrets
from passlib.context import CryptContext
from fast_api.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordManager:

    @staticmethod
    def hash_password(password: str) -> str:
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(
                f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
            )
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def hash_api_key(key: str) -> str:
        return pwd_context.hash(key)

    @staticmethod
    def verify_api_key(plain_key: str, hashed_key: str) -> bool:
        return pwd_context.verify(plain_key, hashed_key)

    @staticmethod
    def generate_api_key() -> str:
        return secrets.token_urlsafe(48)
