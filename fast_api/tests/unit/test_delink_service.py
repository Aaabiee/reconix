import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fast_api.services.delink_service import DelinkService
from fast_api.models.delink_request import DelinkRequestStatus, DelinkRequestType
from fast_api.exceptions import ResourceNotFoundError, ValidationError


class TestRejectDelinkRequest:

    @pytest.mark.asyncio
    async def test_reject_delink_request_changes_status(self, test_db, test_delink_request, test_user):
        service = DelinkService(test_db)
        result = await service.reject_delink_request(
            test_delink_request.id,
            rejected_by=test_user.id,
            reason="Insufficient evidence",
        )
        assert result.status == DelinkRequestStatus.FAILED
        assert result.error_message == "Insufficient evidence"

    @pytest.mark.asyncio
    async def test_reject_nonexistent_request_raises(self, test_db):
        service = DelinkService(test_db)
        with pytest.raises(ResourceNotFoundError):
            await service.reject_delink_request(99999, rejected_by=1)

    @pytest.mark.asyncio
    async def test_reject_non_pending_request_raises(self, test_db, test_delink_request):
        service = DelinkService(test_db)
        await service.reject_delink_request(
            test_delink_request.id, rejected_by=1, reason="first reject"
        )

        with pytest.raises(ValidationError, match="Cannot reject"):
            await service.reject_delink_request(
                test_delink_request.id, rejected_by=1, reason="second attempt"
            )
