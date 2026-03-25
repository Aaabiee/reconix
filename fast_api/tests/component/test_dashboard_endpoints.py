import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestDashboardStats:

    async def test_dashboard_stats(
        self,
        test_client: AsyncClient,
        access_token,
        test_recycled_sim,
        test_delink_request,
        test_nin_linkage,
        test_bvn_linkage,
    ):
        response = await test_client.get(
            "/api/v1/dashboard/stats",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_recycled_sims" in data
        assert "total_cleanup_pending" in data
        assert "total_cleanup_in_progress" in data
        assert "total_cleanup_completed" in data
        assert "total_cleanup_failed" in data
        assert "active_nin_linkages" in data
        assert "active_bvn_linkages" in data
        assert "total_delink_requests" in data
        assert "delink_pending" in data
        assert "delink_completed" in data
        assert "delink_failed" in data
        assert data["total_recycled_sims"] >= 1
        assert data["active_nin_linkages"] >= 1
        assert data["active_bvn_linkages"] >= 1
        assert data["total_delink_requests"] >= 1

    async def test_dashboard_stats_empty_db(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/dashboard/stats",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["total_recycled_sims"], int)
        assert data["total_recycled_sims"] >= 0


@pytest.mark.asyncio
class TestDashboardTrends:

    async def test_dashboard_trends_default(
        self, test_client: AsyncClient, access_token, test_recycled_sim
    ):
        response = await test_client.get(
            "/api/v1/dashboard/trends",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert data["period_days"] == 30
        assert "sims_created_in_period" in data
        assert "delinks_created_in_period" in data
        assert "start_date" in data
        assert "end_date" in data

    async def test_dashboard_trends_custom_days(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/dashboard/trends?days=7",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 7

    async def test_dashboard_trends_max_days_bounded(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/dashboard/trends?days=91",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 422

    async def test_dashboard_trends_zero_days(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/dashboard/trends?days=0",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestDashboardAuth:

    async def test_dashboard_requires_auth(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/dashboard/stats")
        assert response.status_code in [401, 403]

    async def test_dashboard_trends_requires_auth(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/dashboard/trends")
        assert response.status_code in [401, 403]
