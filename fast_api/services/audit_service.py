from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from fast_api.db import BaseRepository
from fast_api.models.audit_log import AuditLog

AUDIT_PII_KEYS = frozenset({
    "password", "hashed_password", "token", "access_token",
    "refresh_token", "api_key", "secret", "secret_key",
    "authorization", "cookie", "x-api-key",
    "nin", "bvn", "previous_owner_nin",
})


def _mask_audit_value(data: dict[str, Any] | None, depth: int = 0) -> dict[str, Any] | None:
    if data is None or depth > 5:
        return data
    masked = {}
    for key, value in data.items():
        if key.lower() in AUDIT_PII_KEYS:
            masked[key] = "[REDACTED]"
        elif isinstance(value, dict):
            masked[key] = _mask_audit_value(value, depth + 1)
        elif isinstance(value, str) and len(value) == 11 and value.isdigit():
            masked[key] = value[:3] + "****" + value[-4:]
        else:
            masked[key] = value
    return masked


class AuditService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = BaseRepository(db, AuditLog)

    async def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: int | None = None,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        audit_data = {
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "user_id": user_id,
            "old_value": _mask_audit_value(old_value),
            "new_value": _mask_audit_value(new_value),
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        audit_log = await self.repository.create(audit_data)
        await self.db.commit()
        return audit_log

    async def get_audit_log_by_id(self, log_id: int) -> AuditLog | None:
        return await self.repository.get_by_id(log_id)

    async def get_all_audit_logs(
        self, skip: int = 0, limit: int = 50, filters: dict[str, Any] | None = None
    ) -> list[AuditLog]:
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)

    async def get_logs_by_resource(
        self, resource_type: str, resource_id: str, skip: int = 0, limit: int = 50
    ) -> list[AuditLog]:
        return await self.get_all_audit_logs(
            skip=skip,
            limit=limit,
            filters={"resource_type": resource_type, "resource_id": resource_id},
        )

    async def get_logs_by_user(
        self, user_id: int, skip: int = 0, limit: int = 50
    ) -> list[AuditLog]:
        return await self.get_all_audit_logs(
            skip=skip, limit=limit, filters={"user_id": user_id}
        )

    async def get_logs_by_action(
        self, action: str, skip: int = 0, limit: int = 50
    ) -> list[AuditLog]:
        return await self.get_all_audit_logs(
            skip=skip, limit=limit, filters={"action": action}
        )

    async def count_audit_logs(
        self, filters: dict[str, Any] | None = None
    ) -> int:
        return await self.repository.count(filters=filters)
