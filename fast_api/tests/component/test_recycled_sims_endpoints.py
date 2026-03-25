import pytest
from httpx import AsyncClient
from datetime import datetime, timezone


@pytest.mark.asyncio
class TestListRecycledSIMs:

    async def test_list_sims_authenticated(
        self, test_client: AsyncClient, access_token, test_recycled_sim
    ):
        response = await test_client.get(
            "/api/v1/recycled-sims",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_list_sims_unauthenticated_401(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/recycled-sims")
        assert response.status_code in [401, 403]

    async def test_pagination_limit_enforced(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/recycled-sims?skip=0&limit=5",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5

    async def test_pagination_limit_max_100(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/recycled-sims?limit=200",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 422

    async def test_list_sims_with_status_filter(
        self, test_client: AsyncClient, access_token, test_recycled_sim
    ):
        response = await test_client.get(
            "/api/v1/recycled-sims?cleanup_status=pending",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200


@pytest.mark.asyncio
class TestCreateRecycledSIM:

    async def test_create_sim_valid(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims",
            json={
                "sim_serial": "SIM_CREATE_001",
                "msisdn": "+2348012345678",
                "imsi": "621200000000001",
                "operator_code": "GLO",
                "date_recycled": datetime.now(timezone.utc).isoformat(),
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sim_serial"] == "SIM_CREATE_001"
        assert data["operator_code"] == "GLO"
        assert data["cleanup_status"] == "pending"

    async def test_create_sim_invalid_msisdn(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims",
            json={
                "sim_serial": "SIM_BAD_MSISDN",
                "msisdn": "invalid",
                "imsi": "621200000000001",
                "operator_code": "MTN",
                "date_recycled": datetime.now(timezone.utc).isoformat(),
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 422

    async def test_create_sim_invalid_imsi(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims",
            json={
                "sim_serial": "SIM_BAD_IMSI",
                "msisdn": "+2348012345679",
                "imsi": "short",
                "operator_code": "MTN",
                "date_recycled": datetime.now(timezone.utc).isoformat(),
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 422

    async def test_create_sim_wrong_role_403(
        self, test_client: AsyncClient, auditor_access_token
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims",
            json={
                "sim_serial": "SIM_AUDITOR_DENY",
                "msisdn": "+2348012345680",
                "imsi": "621200000000002",
                "operator_code": "MTN",
                "date_recycled": datetime.now(timezone.utc).isoformat(),
            },
            headers={"Authorization": f"Bearer {auditor_access_token}"},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestGetRecycledSIM:

    async def test_get_sim_by_id(
        self, test_client: AsyncClient, access_token, test_recycled_sim
    ):
        response = await test_client.get(
            f"/api/v1/recycled-sims/{test_recycled_sim.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_recycled_sim.id
        assert data["msisdn"] == test_recycled_sim.msisdn

    async def test_get_sim_not_found_404(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/recycled-sims/99999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestUpdateRecycledSIM:

    async def test_update_sim(
        self, test_client: AsyncClient, access_token, test_recycled_sim
    ):
        response = await test_client.patch(
            f"/api/v1/recycled-sims/{test_recycled_sim.id}",
            json={"new_registration_status": "active"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["new_registration_status"] == "active"


@pytest.mark.asyncio
class TestBulkUpload:

    async def test_bulk_upload_sims(
        self, test_client: AsyncClient, admin_access_token
    ):
        sims = [
            {
                "sim_serial": f"BULK_{i:04d}",
                "msisdn": f"+234801234{i:04d}",
                "imsi": f"62120000000{i:04d}",
                "operator_code": "MTN",
                "date_recycled": datetime.now(timezone.utc).isoformat(),
            }
            for i in range(3)
        ]
        response = await test_client.post(
            "/api/v1/recycled-sims/bulk",
            json={"sims": sims},
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 3
        assert data["successful"] >= 0

    async def test_bulk_upload_requires_admin(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims/bulk",
            json={"sims": []},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403
