from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from datetime import datetime, timezone
from fast_api.db import BaseRepository
from fast_api.models.notification import (
    Notification,
    NotificationStatus,
    NotificationRecipientType,
    NotificationChannel,
)
from fast_api.exceptions import ResourceNotFoundError


class NotificationService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = BaseRepository(db, Notification)

    async def create_notification(
        self,
        delink_request_id: int,
        recipient_type: NotificationRecipientType,
        channel: NotificationChannel,
        recipient_address: str,
        message_template: str | None = None,
    ) -> Notification:
        notification_data = {
            "delink_request_id": delink_request_id,
            "recipient_type": recipient_type,
            "channel": channel,
            "recipient_address": recipient_address,
            "status": NotificationStatus.PENDING,
            "message_template": message_template,
        }

        notification = await self.repository.create(notification_data)
        await self.db.commit()
        return notification

    async def get_notification_by_id(self, notification_id: int) -> Notification | None:
        return await self.repository.get_by_id(notification_id)

    async def get_all_notifications(
        self, skip: int = 0, limit: int = 50, filters: dict[str, Any] = None
    ) -> list[Notification]:
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)

    async def mark_sent(self, notification_id: int) -> Notification | None:
        notification = await self.get_notification_by_id(notification_id)
        if not notification:
            return None

        updated = await self.repository.update(
            notification_id,
            {
                "status": NotificationStatus.SENT,
                "sent_at": datetime.now(timezone.utc),
            },
        )
        await self.db.commit()
        return updated

    async def mark_delivered(self, notification_id: int) -> Notification | None:
        notification = await self.get_notification_by_id(notification_id)
        if not notification:
            return None

        updated = await self.repository.update(
            notification_id,
            {
                "status": NotificationStatus.DELIVERED,
                "delivered_at": datetime.now(timezone.utc),
            },
        )
        await self.db.commit()
        return updated

    async def mark_failed(self, notification_id: int) -> Notification | None:
        notification = await self.get_notification_by_id(notification_id)
        if not notification:
            return None

        updated = await self.repository.update(
            notification_id,
            {"status": NotificationStatus.FAILED},
        )
        await self.db.commit()
        return updated

    async def get_pending_notifications(
        self, skip: int = 0, limit: int = 100
    ) -> list[Notification]:
        return await self.get_all_notifications(
            skip=skip, limit=limit, filters={"status": NotificationStatus.PENDING}
        )

    async def count_notifications(
        self, filters: dict[str, Any] = None
    ) -> int:
        return await self.repository.count(filters=filters)
