from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field
from fast_api.config import get_settings

settings = get_settings()


class LoginRequest(BaseModel):

    email: EmailStr
    password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH)


class RefreshTokenRequest(BaseModel):

    refresh_token: str


class TokenResponse(BaseModel):

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
