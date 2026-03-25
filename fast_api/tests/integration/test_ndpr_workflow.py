import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestNDPRWorkflow:

    async def test_full_data_subject_workflow(
        self, test_client: AsyncClient, access_token, test_user
    ):
        policy_resp = await test_client.get("/api/v1/data-subject/privacy-policy")
        assert policy_resp.status_code == 200
        policy = policy_resp.json()
        assert "NDPR" in policy["regulation"]

        consent_resp = await test_client.get(
            "/api/v1/data-subject/consent",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert consent_resp.status_code == 200
        consent = consent_resp.json()
        assert consent["consent_given"] is True
        assert len(consent["purposes"]) >= 2

        data_resp = await test_client.get(
            "/api/v1/data-subject/my-data",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert data_resp.status_code == 200
        data = data_resp.json()
        assert data["email"] == test_user.email
        assert "NDPR" in data["data_retention_policy"]

        access_req_resp = await test_client.post(
            "/api/v1/data-subject/access-request",
            json={
                "email": test_user.email,
                "request_type": "access",
                "reason": "Personal data review",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert access_req_resp.status_code == 200
        access_req = access_req_resp.json()
        assert access_req["status"] == "received"
        assert access_req["request_type"] == "access"

    async def test_data_deletion_request_workflow(
        self, test_client: AsyncClient, access_token
    ):
        delete_resp = await test_client.post(
            "/api/v1/data-subject/delete-my-data",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert delete_resp.status_code == 200
        delete_data = delete_resp.json()
        assert delete_data["status"] == "queued"
        assert "NDPR" in delete_data["retention_notice"]
        assert len(delete_data["request_id"]) > 0

    async def test_data_portability_request(
        self, test_client: AsyncClient, access_token
    ):
        resp = await test_client.post(
            "/api/v1/data-subject/access-request",
            json={
                "email": "test@example.com",
                "request_type": "portability",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["request_type"] == "portability"

    async def test_unauthenticated_access_blocked(self, test_client: AsyncClient):
        endpoints = [
            ("GET", "/api/v1/data-subject/my-data"),
            ("GET", "/api/v1/data-subject/consent"),
            ("POST", "/api/v1/data-subject/delete-my-data"),
        ]
        for method, path in endpoints:
            if method == "GET":
                resp = await test_client.get(path)
            else:
                resp = await test_client.post(path)
            assert resp.status_code in [401, 403], f"{method} {path} should require auth"

    async def test_privacy_policy_no_auth_required(self, test_client: AsyncClient):
        resp = await test_client.get("/api/v1/data-subject/privacy-policy")
        assert resp.status_code == 200


@pytest.mark.asyncio
class TestNDPRSecurityControls:

    async def test_xss_in_access_request_reason(
        self, test_client: AsyncClient, access_token
    ):
        resp = await test_client.post(
            "/api/v1/data-subject/access-request",
            json={
                "email": "test@example.com",
                "request_type": "access",
                "reason": "<script>alert('xss')</script>",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code in [200, 400]

    async def test_invalid_request_type_rejected(
        self, test_client: AsyncClient, access_token
    ):
        resp = await test_client.post(
            "/api/v1/data-subject/access-request",
            json={
                "email": "test@example.com",
                "request_type": "'; DROP TABLE users; --",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code in [400, 422]

    async def test_oversized_reason_rejected(
        self, test_client: AsyncClient, access_token
    ):
        resp = await test_client.post(
            "/api/v1/data-subject/access-request",
            json={
                "email": "test@example.com",
                "request_type": "access",
                "reason": "x" * 1001,
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 422
