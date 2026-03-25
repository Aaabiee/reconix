from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from fast_api.db import BaseRepository
from fast_api.models.user import User
from fast_api.schemas.user import UserCreate, UserUpdate
from fast_api.auth.authlib.password import PasswordManager
from fast_api.exceptions import ConflictError, ResourceNotFoundError


class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = BaseRepository(db, User)

    async def create_user(self, user_in: UserCreate) -> User:
        exists = await self.repository.exists(email=user_in.email)
        if exists:
            raise ConflictError(
                f"User with email {user_in.email} already exists", resource_type="User"
            )

        hashed_password = PasswordManager.hash_password(user_in.password)
        user_data = {
            "email": user_in.email,
            "hashed_password": hashed_password,
            "full_name": user_in.full_name,
            "organization": user_in.organization,
        }

        user = await self.repository.create(user_data)
        await self.db.commit()
        return user

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.repository.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, user_in: UserUpdate) -> User:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", user_id)

        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = PasswordManager.hash_password(
                update_data.pop("password")
            )

        updated_user = await self.repository.update(user_id, update_data)
        await self.db.commit()
        return updated_user

    async def delete_user(self, user_id: int) -> bool:
        deleted = await self.repository.delete(user_id)
        if deleted:
            await self.db.commit()
        return deleted

    async def authenticate_user(self, email: str, password: str) -> User | None:
        user = await self.get_user_by_email(email)
        if not user:
            return None

        if not PasswordManager.verify_password(password, user.hashed_password):
            return None

        return user

    async def lock_user_account(self, user_id: int, minutes: int = 15) -> None:
        unlock_time = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        await self.repository.update(
            user_id, {"locked_until": unlock_time, "failed_login_attempts": 5}
        )
        await self.db.commit()

    async def reset_login_attempts(self, user_id: int) -> None:
        await self.repository.update(user_id, {"failed_login_attempts": 0})
        await self.db.commit()

    async def increment_login_attempts(self, user_id: int) -> int:
        user = await self.get_user_by_id(user_id)
        if user:
            new_count = user.failed_login_attempts + 1
            await self.repository.update(user_id, {"failed_login_attempts": new_count})
            await self.db.commit()
            return new_count
        return 0
