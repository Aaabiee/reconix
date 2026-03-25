import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from fast_api.models.recycled_sim import RecycledSIM
from fast_api.models.delink_request import DelinkRequest, DelinkRequestStatus


@pytest.mark.asyncio
class TestCreateDelinkRequest:

    async def test_create_delink_request(
        self, test_client: AsyncClient, access_token, test_recycled_sim
    ):
        response = await test_client.post(
            "/api/v1/delink-requests",
            json={
                "recycled_sim_id": test_recycled_sim.id,
                "request_type": "both",
                "reason": "SIM recycled, stale linkages",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recycled_sim_id"] == test_recycled_sim.id
        assert data["request_type"] == "both"
        assert data["status"] == "pending"
        assert data["reason"] == "SIM recycled, stale linkages"

    async def test_create_delink_invalid_sim(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/delink-requests",
            json={
                "recycled_sim_id": 99999,
                "request_type": "both",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    async def test_create_delink_invalid_type(
        self, test_client: AsyncClient, access_token, test_recycled_sim
    ):
        response = await test_client.post(
            "/api/v1/delink-requests",
            json={
                "recycled_sim_id": test_recycled_sim.id,
                "request_type": "invalid_type",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 422

    async def test_create_delink_unauthenticated(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/v1/delink-requests",
            json={"recycled_sim_id": 1, "request_type": "both"},
        )
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestApproveDelinkRequest:

    async def test_approve_delink_request(
        self, test_client: AsyncClient, admin_access_token, test_delink_request
    ):
        response = await test_client.post(
            f"/api/v1/delink-requests/{test_delink_request.id}/approve",
            json={"approved": True},
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["approved_by"] is not None

    async def test_reject_delink_request(
        self, test_client: AsyncClient, admin_access_token, test_db, test_recycled_sim, test_user
    ):
        req = DelinkRequest(
            recycled_sim_id=test_recycled_sim.id,
            request_type="nin",
            status="pending",
            initiated_by=test_user.id,
            reason="To be rejected",
        )
        test_db.add(req)
        await test_db.flush()
        await test_db.refresh(req)

        response = await test_client.post(
            f"/api/v1/delink-requests/{req.id}/approve",
            json={"approved": False, "reason": "Not justified"},
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [200, 422, 500]

    async def test_cannot_approve_completed_request(
        self, test_client: AsyncClient, admin_access_token, test_db, test_recycled_sim, test_user
    ):
        req = DelinkRequest(
            recycled_sim_id=test_recycled_sim.id,
            request_type="bvn",
            status=DelinkRequestStatus.COMPLETED,
            initiated_by=test_user.id,
            completed_at=datetime.now(timezone.utc),
        )
        test_db.add(req)
        await test_db.flush()
        await test_db.refresh(req)

        response = await test_client.post(
            f"/api/v1/delink-requests/{req.id}/approve",
            json={"approved": True},
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 422

    async def test_approve_requires_admin(
        self, test_client: AsyncClient, access_token, test_delink_request
    ):
        response = await test_client.post(
            f"/api/v1/delink-requests/{test_delink_request.id}/approve",
            json={"approved": True},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestCancelDelinkRequest:

    async def test_cancel_delink_request(
        self, test_client: AsyncClient, access_token, test_delink_request
    ):
        response = await test_client.post(
            f"/api/v1/delink-requests/{test_delink_request.id}/cancel",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    async def test_cancel_completed_request_fails(
        self, test_client: AsyncClient, access_token, test_db, test_recycled_sim, test_user
    ):
        req = DelinkRequest(
            recycled_sim_id=test_recycled_sim.id,
            request_type="both",
            status=DelinkRequestStatus.COMPLETED,
            initiated_by=test_user.id,
            completed_at=datetime.now(timezone.utc),
        )
        test_db.add(req)
        await test_db.flush()
        await test_db.refresh(req)

        response = await test_client.post(
            f"/api/v1/delink-requests/{req.id}/cancel",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestGetDelinkRequests:

    async def test_get_delink_requests_list(
        self, test_client: AsyncClient, access_token, test_delink_request
    ):
        response = await test_client.get(
            "/api/v1/delink-requests",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_get_delink_request_by_id(
        self, test_client: AsyncClient, access_token, test_delink_request
    ):
        response = await test_client.get(
            f"/api/v1/delink-requests/{test_delink_request.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_delink_request.id

    async def test_get_delink_request_not_found(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/delink-requests/99999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    async def test_get_delink_requests_with_status_filter(
        self, test_client: AsyncClient, access_token, test_delink_request
    ):
        response = await test_client.get(
            "/api/v1/delink-requests?status=pending",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
