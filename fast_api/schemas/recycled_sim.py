from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class RecycledSIMCreate(BaseModel):
    """Recycled SIM creation request schema."""

    sim_serial: str = Field(..., min_length=1, max_length=50)
    msisdn: str = Field(..., pattern=r"^\+?234[0-9]{10}$")
    imsi: str = Field(..., pattern=r"^[0-9]{15}$")
    operator_code: str = Field(..., max_length=10)
    date_recycled: datetime
    date_deactivated: datetime | None = None
    previous_owner_nin: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RecycledSIMUpdate(BaseModel):
    """Recycled SIM update request schema."""

    new_registration_status: str | None = None
    previous_nin_linked: bool | None = None
    previous_bvn_linked: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class RecycledSIMResponse(BaseModel):
    """Recycled SIM response schema."""

    id: int
    sim_serial: str
    msisdn: str
    imsi: str
    operator_code: str
    date_recycled: datetime
    date_deactivated: datetime | None = None
    previous_owner_nin: str | None = None
    new_registration_status: str | None = None
    previous_nin_linked: bool
    previous_bvn_linked: bool
    cleanup_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecycledSIMBulkUpload(BaseModel):
    """Bulk upload recycled SIMs request schema."""

    sims: list[RecycledSIMCreate] = Field(..., max_length=10000)
    checksum: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BulkUploadResponse(BaseModel):
    """Bulk upload response schema."""

    total_records: int
    successful: int
    failed: int
    errors: list[dict] | None = None
