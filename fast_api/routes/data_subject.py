from __future__ import annotations

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fast_api.auth.authlib.oauth2 import get_current_user
from fast_api.auth.authlib.rbac import require_role
from fast_api.db import get_db
from fast_api.exceptions import ResourceNotFoundError, ValidationError
from fast_api.exceptions.handlers import to_http_exception
from fast_api.schemas.data_subject import (
    DataSubjectAccessRequest,
    DataSubjectAccessResponse,
    PersonalDataExport,
    DataDeletionResponse,
)
from fast_api.services.data_subject_service import DataSubjectService
from fast_api.models.user import User
from fast_api.middleware.rate_limiter import limiter

router = APIRouter(prefix="/data-subject", tags=["NDPR compliance"])


@router.post("/access-request", response_model=DataSubjectAccessResponse)
@limiter.limit("5/minute")
async def submit_access_request(
    request: Request,
    body: DataSubjectAccessRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    request_id = uuid.uuid4().hex
    return DataSubjectAccessResponse(
        request_id=request_id,
        status="received",
        request_type=body.request_type,
        submitted_at=datetime.now(timezone.utc),
        estimated_completion="30 days per NDPR guidelines",
    )


@router.get("/my-data", response_model=PersonalDataExport)
@limiter.limit("10/minute")
async def export_personal_data(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = DataSubjectService(db)
        data = await service.get_personal_data(current_user.id)
        return PersonalDataExport(**data)
    except ResourceNotFoundError as e:
        raise to_http_exception(e)


@router.post("/delete-my-data", response_model=DataDeletionResponse)
@limiter.limit("2/hour")
async def request_data_deletion(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = DataSubjectService(db)
        result = await service.request_data_deletion(current_user.id)
        return DataDeletionResponse(**result)
    except (ResourceNotFoundError, ValidationError) as e:
        raise to_http_exception(e)


@router.get("/consent")
@limiter.limit("10/minute")
async def get_consent_record(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = DataSubjectService(db)
        return await service.get_consent_record(current_user.id)
    except ResourceNotFoundError as e:
        raise to_http_exception(e)


@router.get("/privacy-policy")
async def get_privacy_policy(request: Request):
    return {
        "policy_version": "1.0",
        "effective_date": "2024-03-01",
        "data_controller": "Reconix Platform Operator",
        "data_protection_officer": "dpo@reconix.ng",
        "regulation": "Nigeria Data Protection Regulation (NDPR) 2019",
        "supervisory_authority": "Nigeria Data Protection Bureau (NDPB)",
        "purposes_of_processing": [
            "Identity reconciliation for recycled SIM card management",
            "NIN/BVN linkage verification with NIMC and NIBSS",
            "Audit trail maintenance for regulatory compliance",
            "Notification delivery to affected parties",
        ],
        "legal_basis": [
            "NDPR Section 2.2 — Consent",
            "NDPR Section 2.2 — Legitimate interest",
            "NDPR Section 2.2 — Legal obligation (CBN/NCC regulations)",
        ],
        "data_categories": [
            "Identity data (name, email, organization)",
            "Authentication data (hashed credentials, login timestamps)",
            "Operational data (SIM records, linkage data, delink requests)",
            "Audit data (action logs, IP addresses)",
        ],
        "retention_periods": {
            "audit_logs": "365 days (configurable)",
            "user_accounts": "Duration of service + 90 days",
            "operational_data": "As required by regulatory mandate",
        },
        "data_subject_rights": [
            "Right of access (GET /api/v1/data-subject/my-data)",
            "Right to rectification (contact DPO)",
            "Right to erasure (POST /api/v1/data-subject/delete-my-data)",
            "Right to data portability (GET /api/v1/data-subject/my-data)",
            "Right to object (contact DPO)",
            "Right to withdraw consent (contact DPO)",
        ],
        "cross_border_transfers": "Data processed within Nigeria. No cross-border transfers without NDPB approval.",
        "security_measures": [
            "Encryption at rest (HMAC-SHA256)",
            "Encryption in transit (TLS 1.2+)",
            "Role-based access control (4 roles, 19 permissions)",
            "PII masking in logs",
            "Immutable audit trail",
        ],
    }
