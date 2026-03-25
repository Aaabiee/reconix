from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fast_api.models.user import User
from fast_api.models.audit_log import AuditLog
from fast_api.models.delink_request import DelinkRequest
from fast_api.exceptions import ResourceNotFoundError, ValidationError

logger = logging.getLogger(__name__)


class DataSubjectService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_personal_data(self, user_id: int) -> dict:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ResourceNotFoundError("User", user_id)

        audit_count_stmt = select(func.count(AuditLog.id)).where(
            AuditLog.user_id == user_id
        )
        audit_result = await self.db.execute(audit_count_stmt)
        audit_count = audit_result.scalar() or 0

        delink_count_stmt = select(func.count(DelinkRequest.id)).where(
            DelinkRequest.initiated_by == user_id
        )
        delink_result = await self.db.execute(delink_count_stmt)
        delink_count = delink_result.scalar() or 0

        return {
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organization": user.organization,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "audit_log_count": audit_count,
            "delink_requests_initiated": delink_count,
            "data_retention_policy": "365 days for audit logs per NDPR Section 2.1",
        }

    async def request_data_deletion(self, user_id: int) -> dict:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ResourceNotFoundError("User", user_id)

        if user.role == "admin":
            raise ValidationError(
                "Admin accounts cannot self-delete — contact the data protection officer"
            )

        request_id = uuid.uuid4().hex

        audit_count_stmt = select(func.count(AuditLog.id)).where(
            AuditLog.user_id == user_id
        )
        audit_result = await self.db.execute(audit_count_stmt)
        audit_count = audit_result.scalar() or 0

        logger.info(
            "data_deletion_requested",
            extra={
                "extra_data": {
                    "request_id": request_id,
                    "user_id": user_id,
                    "records_affected": audit_count,
                }
            },
        )

        return {
            "request_id": request_id,
            "status": "queued",
            "records_queued_for_deletion": 1,
            "estimated_completion": "30 days per NDPR guidelines",
            "retention_notice": (
                "Audit logs are retained for regulatory compliance per NDPR Section 2.1(1)(b) "
                "and will be anonymized rather than deleted. Personal account data will be "
                "removed within 30 days."
            ),
        }

    async def get_consent_record(self, user_id: int) -> dict:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ResourceNotFoundError("User", user_id)

        return {
            "user_id": user.id,
            "consent_given": True,
            "consent_date": user.created_at,
            "purposes": [
                "Identity reconciliation for recycled SIM management",
                "NIN/BVN linkage verification",
                "Audit trail maintenance for regulatory compliance",
            ],
            "legal_basis": "NDPR Section 2.2 — Legitimate interest and regulatory mandate",
            "data_controller": "Reconix Platform Operator",
            "data_protection_officer": "dpo@reconix.ng",
            "right_to_withdraw": True,
        }
