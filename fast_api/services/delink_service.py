from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any
from datetime import datetime, timezone
from fast_api.db import BaseRepository
from fast_api.models.delink_request import (
    DelinkRequest,
    DelinkRequestStatus,
    DelinkRequestType,
)
from fast_api.models.notification import Notification, NotificationStatus
from fast_api.models.recycled_sim import RecycledSIM, CleanupStatus
from fast_api.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    AuthorizationError,
)


class DelinkService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.delink_repo = BaseRepository(db, DelinkRequest)
        self.sim_repo = BaseRepository(db, RecycledSIM)

    async def create_delink_request(
        self,
        recycled_sim_id: int,
        request_type: DelinkRequestType,
        initiated_by: int,
        reason: str | None = None,
    ) -> DelinkRequest:
        sim = await self.sim_repo.get_by_id(recycled_sim_id)
        if not sim:
            raise ResourceNotFoundError("RecycledSIM", recycled_sim_id)

        delink_data = {
            "recycled_sim_id": recycled_sim_id,
            "request_type": request_type,
            "status": DelinkRequestStatus.PENDING,
            "initiated_by": initiated_by,
            "reason": reason,
        }

        delink_request = await self.delink_repo.create(delink_data)
        await self.db.commit()
        return delink_request

    async def get_delink_request_by_id(self, request_id: int) -> DelinkRequest | None:
        return await self.delink_repo.get_by_id(request_id)

    async def get_all_delink_requests(
        self, skip: int = 0, limit: int = 50, filters: dict[str, Any] = None
    ) -> list[DelinkRequest]:
        return await self.delink_repo.get_all(skip=skip, limit=limit, filters=filters)

    async def approve_delink_request(
        self, request_id: int, approved_by: int
    ) -> DelinkRequest:
        delink_request = await self.get_delink_request_by_id(request_id)
        if not delink_request:
            raise ResourceNotFoundError("DelinkRequest", request_id)

        if delink_request.status != DelinkRequestStatus.PENDING:
            raise ValidationError(
                f"Cannot approve request with status {delink_request.status}"
            )

        updated = await self.delink_repo.update(
            request_id,
            {
                "status": DelinkRequestStatus.PROCESSING,
                "approved_by": approved_by,
            },
        )
        await self.db.commit()
        return updated

    async def complete_delink_request(self, request_id: int) -> DelinkRequest:
        delink_request = await self.get_delink_request_by_id(request_id)
        if not delink_request:
            raise ResourceNotFoundError("DelinkRequest", request_id)

        sim = await self.sim_repo.get_by_id(delink_request.recycled_sim_id)

        if sim:
            from fast_api.services.linkage_service import NINLinkageService, BVNLinkageService
            request_type = delink_request.request_type

            if request_type in (DelinkRequestType.NIN, DelinkRequestType.BOTH):
                nin_service = NINLinkageService(self.db)
                nin_linkage = await nin_service.get_active_linkage_for_msisdn(sim.msisdn)
                if nin_linkage:
                    await nin_service.unlink(nin_linkage.id)

            if request_type in (DelinkRequestType.BVN, DelinkRequestType.BOTH):
                bvn_service = BVNLinkageService(self.db)
                bvn_linkage = await bvn_service.get_active_linkage_for_msisdn(sim.msisdn)
                if bvn_linkage:
                    await bvn_service.unlink(bvn_linkage.id)

            await self.sim_repo.update(
                sim.id, {
                    "cleanup_status": CleanupStatus.COMPLETED,
                    "previous_nin_linked": False,
                    "previous_bvn_linked": False,
                }
            )

            await self._create_completion_notifications(delink_request, sim)

        updated = await self.delink_repo.update(
            request_id,
            {
                "status": DelinkRequestStatus.COMPLETED,
                "completed_at": datetime.now(timezone.utc),
            },
        )
        await self.db.commit()
        return updated

    async def _create_completion_notifications(
        self, delink_request: DelinkRequest, sim: RecycledSIM
    ) -> None:
        from fast_api.db import BaseRepository
        from fast_api.models.notification import Notification

        notification_repo = BaseRepository(self.db, Notification)

        recipients = [
            {
                "recipient_type": "former_owner",
                "channel": "sms",
                "recipient_address": sim.msisdn,
                "message_template": "delink_complete_former_owner",
            },
            {
                "recipient_type": "bank",
                "channel": "api_callback",
                "recipient_address": f"bank_for_{sim.msisdn}",
                "message_template": "delink_complete_bank",
            },
            {
                "recipient_type": "nimc",
                "channel": "api_callback",
                "recipient_address": "nimc_delink_endpoint",
                "message_template": "delink_complete_nimc",
            },
        ]

        for r in recipients:
            await notification_repo.create({
                "delink_request_id": delink_request.id,
                "recipient_type": r["recipient_type"],
                "channel": r["channel"],
                "recipient_address": r["recipient_address"],
                "status": "pending",
                "message_template": r["message_template"],
            })

    async def fail_delink_request(
        self, request_id: int, error_message: str
    ) -> DelinkRequest:
        delink_request = await self.get_delink_request_by_id(request_id)
        if not delink_request:
            raise ResourceNotFoundError("DelinkRequest", request_id)

        sim = await self.sim_repo.get_by_id(delink_request.recycled_sim_id)
        if sim:
            await self.sim_repo.update(
                sim.id, {"cleanup_status": CleanupStatus.FAILED}
            )

        updated = await self.delink_repo.update(
            request_id,
            {
                "status": DelinkRequestStatus.FAILED,
                "error_message": error_message,
                "completed_at": datetime.now(timezone.utc),
            },
        )
        await self.db.commit()
        return updated

    async def reject_delink_request(
        self, request_id: int, rejected_by: int, reason: str = "Rejected by admin"
    ) -> DelinkRequest:
        delink_request = await self.get_delink_request_by_id(request_id)
        if not delink_request:
            raise ResourceNotFoundError("DelinkRequest", request_id)

        if delink_request.status != DelinkRequestStatus.PENDING:
            raise ValidationError(
                f"Cannot reject request with status {delink_request.status}"
            )

        updated = await self.delink_repo.update(
            request_id,
            {
                "status": DelinkRequestStatus.FAILED,
                "approved_by": rejected_by,
                "error_message": reason,
                "completed_at": datetime.now(timezone.utc),
            },
        )
        await self.db.commit()
        return updated

    async def cancel_delink_request(self, request_id: int) -> DelinkRequest:
        delink_request = await self.get_delink_request_by_id(request_id)
        if not delink_request:
            raise ResourceNotFoundError("DelinkRequest", request_id)

        if delink_request.status not in [
            DelinkRequestStatus.PENDING,
            DelinkRequestStatus.PROCESSING,
        ]:
            raise ValidationError(
                f"Cannot cancel request with status {delink_request.status}"
            )

        updated = await self.delink_repo.update(
            request_id,
            {
                "status": DelinkRequestStatus.CANCELLED,
                "completed_at": datetime.now(timezone.utc),
            },
        )
        await self.db.commit()
        return updated

    async def count_delink_requests(
        self, filters: dict[str, Any] = None
    ) -> int:
        return await self.delink_repo.count(filters=filters)
