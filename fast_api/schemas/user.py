from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime


class UserCreate(BaseModel):
    """User creation request schema."""

    email: EmailStr
    password: str = Field(..., min_length=12)
    full_name: str = Field(..., min_length=3, max_length=255)
    organization: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """User update request schema."""

    full_name: str | None = None
    organization: str | None = None
    password: str | None = Field(None, min_length=12)

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """User response schema."""

    id: int
    email: str
    full_name: str
    role: str
    organization: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
