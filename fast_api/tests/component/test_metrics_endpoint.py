import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestMetricsEndpoint:

    async def test_metrics_endpoint_returns_200(self, test_client: AsyncClient):
        response = await test_client.get("/metrics")
        assert response.status_code == 200

    async def test_metrics_returns_prometheus_format(self, test_client: AsyncClient):
        response = await test_client.get("/metrics")
        text = response.text
        assert "reconix_http_requests_total" in text
        assert "reconix_http_active_requests" in text

    async def test_metrics_tracks_request(self, test_client: AsyncClient, access_token, test_recycled_sim):
        await test_client.get(
            "/api/v1/recycled-sims",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response = await test_client.get("/metrics")
        assert "reconix_http_requests_total" in response.text

    async def test_metrics_does_not_require_auth(self, test_client: AsyncClient):
        response = await test_client.get("/metrics")
        assert response.status_code == 200
