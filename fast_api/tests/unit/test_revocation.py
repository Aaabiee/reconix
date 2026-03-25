import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from fast_api.services.token_revocation_service import TokenRevocationService


class TestTokenRevocationValidation:

    @pytest.mark.asyncio
    async def test_cleanup_expired_returns_count(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        service = TokenRevocationService(mock_db)
        count = await service.cleanup_expired()
        assert count == 5
