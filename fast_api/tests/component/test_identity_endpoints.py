import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestIdentityLookup:

    async def test_lookup_requires_auth(self, test_client: AsyncClient):
        response = await test_client.get(
            "/api/v1/identity/lookup?msisdn=+2348012345678"
        )
        assert response.status_code in [401, 403]

    async def test_lookup_returns_mapping(
        self, test_client: AsyncClient, access_token, test_recycled_sim, test_nin_linkage
    ):
        response = await test_client.get(
            f"/api/v1/identity/lookup?msisdn={test_recycled_sim.msisdn}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["msisdn"] == test_recycled_sim.msisdn
        assert data["is_recycled"] is True
        assert data["nin_linkage_active"] is True
        assert data["confidence_score"] > 0
        assert data["sources_consulted"] is not None
        assert data["assessed_at"] is not None

    async def test_lookup_unknown_msisdn(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/identity/lookup?msisdn=+2349099999999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_recycled"] is False
        assert data["nin"] is None
        assert data["bvn"] is None
        assert data["confidence_score"] < 0.5

    async def test_lookup_invalid_msisdn(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/identity/lookup?msisdn=invalid",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
class TestBatchLookup:

    async def test_batch_requires_admin_or_operator(
        self, test_client: AsyncClient, auditor_access_token
    ):
        response = await test_client.post(
            "/api/v1/identity/batch-lookup",
            json={"msisdns": ["+2348012345678"]},
            headers={"Authorization": f"Bearer {auditor_access_token}"},
        )
        assert response.status_code == 403

    async def test_batch_returns_mappings(
        self, test_client: AsyncClient, access_token, test_recycled_sim
    ):
        response = await test_client.post(
            "/api/v1/identity/batch-lookup",
            json={"msisdns": [test_recycled_sim.msisdn]},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["mappings"]) == 1

    async def test_batch_rejects_over_100(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/identity/batch-lookup",
            json={"msisdns": [f"+234801234{i:04d}" for i in range(101)]},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code in [400, 422]

    async def test_batch_rejects_empty_list(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/identity/batch-lookup",
            json={"msisdns": []},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
class TestCorroborate:

    async def test_corroborate_requires_admin(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/identity/corroborate?msisdn=+2348012345678",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403

    async def test_corroborate_returns_local_data(
        self, test_client: AsyncClient, admin_access_token, test_recycled_sim
    ):
        response = await test_client.get(
            f"/api/v1/identity/corroborate?msisdn={test_recycled_sim.msisdn}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["msisdn"] == test_recycled_sim.msisdn
        assert data["sources_consulted"] is not None


@pytest.mark.asyncio
class TestConflicts:

    async def test_conflicts_requires_admin_or_auditor(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/identity/conflicts",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403

    async def test_conflicts_accessible_by_admin(
        self, test_client: AsyncClient, admin_access_token
    ):
        response = await test_client.get(
            "/api/v1/identity/conflicts",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "conflicts" in data
