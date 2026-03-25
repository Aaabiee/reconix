import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoint:

    async def test_health_check_returns_200(self, test_client: AsyncClient):
        response = await test_client.get("/health")
        assert response.status_code == 200

    async def test_health_includes_pool_info(self, test_client: AsyncClient):
        response = await test_client.get("/health")
        data = response.json()
        assert "pool" in data
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    async def test_health_includes_version(self, test_client: AsyncClient):
        response = await test_client.get("/health")
        data = response.json()
        assert data["version"] == "1.0.0"
