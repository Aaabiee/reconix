import pytest
from httpx import AsyncClient
from datetime import datetime, timezone


@pytest.mark.asyncio
class TestRecycledSimIDOR:

    async def test_get_sim_returns_404_for_nonexistent(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/recycled-sims/999999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code in [404, 422]

    async def test_unauthenticated_cannot_access_sim(
        self, test_client: AsyncClient, test_recycled_sim
    ):
        response = await test_client.get(
            f"/api/v1/recycled-sims/{test_recycled_sim.id}",
        )
        assert response.status_code in [401, 403]

    async def test_patch_requires_admin_or_operator(
        self, test_client: AsyncClient, auditor_access_token, test_recycled_sim
    ):
        response = await test_client.patch(
            f"/api/v1/recycled-sims/{test_recycled_sim.id}",
            json={"cleanup_status": "completed"},
            headers={"Authorization": f"Bearer {auditor_access_token}"},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestDelinkRequestIDOR:

    async def test_get_delink_returns_404_for_nonexistent(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/delink-requests/999999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code in [404, 422]

    async def test_approve_requires_admin(
        self, test_client: AsyncClient, access_token, test_delink_request
    ):
        response = await test_client.post(
            f"/api/v1/delink-requests/{test_delink_request.id}/approve",
            json={"approved": True},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403

    async def test_cancel_requires_admin_or_operator(
        self, test_client: AsyncClient, auditor_access_token, test_delink_request
    ):
        response = await test_client.post(
            f"/api/v1/delink-requests/{test_delink_request.id}/cancel",
            headers={"Authorization": f"Bearer {auditor_access_token}"},
        )
        assert response.status_code == 403

    async def test_unauthenticated_cannot_list(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/delink-requests")
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestNotificationIDOR:

    async def test_get_notification_returns_404_for_nonexistent(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/notifications/999999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code in [404, 422]

    async def test_send_notification_requires_admin_or_operator(
        self, test_client: AsyncClient, auditor_access_token
    ):
        response = await test_client.post(
            "/api/v1/notifications",
            json={
                "delink_request_id": 1,
                "recipient_type": "former_owner",
                "channel": "email",
                "recipient_address": "test@example.com",
                "message_template": "delink_notice",
            },
            headers={"Authorization": f"Bearer {auditor_access_token}"},
        )
        assert response.status_code == 403

    async def test_unauthenticated_cannot_access_notifications(
        self, test_client: AsyncClient
    ):
        response = await test_client.get("/api/v1/notifications")
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestBulkUploadIDOR:

    async def test_bulk_upload_requires_admin(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims/bulk",
            json={"sims": []},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403
