from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from fast_api.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class RetentionService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def purge_expired_audit_logs(self, retention_days: int) -> int:
        if retention_days < 1:
            raise ValueError("retention_days must be at least 1")

        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        stmt = delete(AuditLog).where(AuditLog.created_at < cutoff)
        result = await self.db.execute(stmt)
        await self.db.commit()

        deleted_count = result.rowcount or 0
        logger.info(
            "audit_log_purge completed",
            extra={
                "extra_data": {
                    "retention_days": retention_days,
                    "cutoff_date": cutoff.isoformat(),
                    "deleted_count": deleted_count,
                }
            },
        )
        return deleted_count
