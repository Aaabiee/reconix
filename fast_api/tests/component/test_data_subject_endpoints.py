import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestPrivacyPolicy:

    async def test_privacy_policy_public_access(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/data-subject/privacy-policy")
        assert response.status_code == 200
        data = response.json()
        assert data["regulation"] == "Nigeria Data Protection Regulation (NDPR) 2019"
        assert "purposes_of_processing" in data
        assert "data_subject_rights" in data
        assert "retention_periods" in data
        assert "security_measures" in data
        assert data["data_protection_officer"] == "dpo@reconix.ng"

    async def test_privacy_policy_has_legal_basis(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/data-subject/privacy-policy")
        data = response.json()
        assert len(data["legal_basis"]) >= 3
        assert any("Consent" in basis for basis in data["legal_basis"])
        assert any("Legitimate interest" in basis for basis in data["legal_basis"])

    async def test_privacy_policy_has_cross_border_info(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/data-subject/privacy-policy")
        data = response.json()
        assert "cross_border_transfers" in data
        assert "Nigeria" in data["cross_border_transfers"]


@pytest.mark.asyncio
class TestMyData:

    async def test_my_data_requires_auth(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/data-subject/my-data")
        assert response.status_code in [401, 403]

    async def test_my_data_returns_personal_data(
        self, test_client: AsyncClient, access_token, test_user
    ):
        response = await test_client.get(
            "/api/v1/data-subject/my-data",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["role"] == test_user.role
        assert "data_retention_policy" in data
        assert "NDPR" in data["data_retention_policy"]

    async def test_my_data_includes_activity_counts(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/data-subject/my-data",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = response.json()
        assert "audit_log_count" in data
        assert "delink_requests_initiated" in data
        assert isinstance(data["audit_log_count"], int)


@pytest.mark.asyncio
class TestDeleteMyData:

    async def test_delete_requires_auth(self, test_client: AsyncClient):
        response = await test_client.post("/api/v1/data-subject/delete-my-data")
        assert response.status_code in [401, 403]

    async def test_delete_returns_queued_response(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/data-subject/delete-my-data",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert "request_id" in data
        assert "NDPR" in data["retention_notice"]

    async def test_admin_cannot_self_delete(
        self, test_client: AsyncClient, admin_access_token
    ):
        response = await test_client.post(
            "/api/v1/data-subject/delete-my-data",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
class TestConsent:

    async def test_consent_requires_auth(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/data-subject/consent")
        assert response.status_code in [401, 403]

    async def test_consent_returns_record(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/data-subject/consent",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["consent_given"] is True
        assert "purposes" in data
        assert "legal_basis" in data
        assert data["right_to_withdraw"] is True
        assert "NDPR" in data["legal_basis"]


@pytest.mark.asyncio
class TestAccessRequest:

    async def test_access_request_requires_auth(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/v1/data-subject/access-request",
            json={"email": "test@example.com", "request_type": "access"},
        )
        assert response.status_code in [401, 403]

    async def test_access_request_valid_types(
        self, test_client: AsyncClient, access_token
    ):
        for req_type in ["access", "deletion", "rectification", "portability"]:
            response = await test_client.post(
                "/api/v1/data-subject/access-request",
                json={"email": "test@example.com", "request_type": req_type},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["request_type"] == req_type
            assert data["status"] == "received"

    async def test_access_request_invalid_type_rejected(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/data-subject/access-request",
            json={"email": "test@example.com", "request_type": "invalid"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 422
