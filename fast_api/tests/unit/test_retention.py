import pytest
from unittest.mock import AsyncMock, MagicMock
from fast_api.services.retention_service import RetentionService


class TestRetentionServiceValidation:

    @pytest.mark.asyncio
    async def test_purge_raises_for_zero_days(self):
        mock_db = AsyncMock()
        service = RetentionService(mock_db)
        with pytest.raises(ValueError, match="retention_days must be at least 1"):
            await service.purge_expired_audit_logs(0)

    @pytest.mark.asyncio
    async def test_purge_raises_for_negative_days(self):
        mock_db = AsyncMock()
        service = RetentionService(mock_db)
        with pytest.raises(ValueError, match="retention_days must be at least 1"):
            await service.purge_expired_audit_logs(-5)
