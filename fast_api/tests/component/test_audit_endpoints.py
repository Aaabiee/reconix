import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestListAuditLogs:

    async def test_list_audit_logs_admin(
        self, test_client: AsyncClient, admin_access_token, test_audit_log
    ):
        response = await test_client.get(
            "/api/v1/audit-logs",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_list_audit_logs_auditor(
        self, test_client: AsyncClient, auditor_access_token, test_audit_log
    ):
        response = await test_client.get(
            "/api/v1/audit-logs",
            headers={"Authorization": f"Bearer {auditor_access_token}"},
        )
        assert response.status_code == 200

    async def test_list_audit_logs_operator_forbidden(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/audit-logs",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403

    async def test_list_audit_logs_unauthenticated(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/audit-logs")
        assert response.status_code in [401, 403]

    async def test_list_audit_logs_with_action_filter(
        self, test_client: AsyncClient, admin_access_token, test_audit_log
    ):
        response = await test_client.get(
            "/api/v1/audit-logs?action=create",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    async def test_list_audit_logs_with_resource_type_filter(
        self, test_client: AsyncClient, admin_access_token, test_audit_log
    ):
        response = await test_client.get(
            "/api/v1/audit-logs?resource_type=RecycledSIM",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200


@pytest.mark.asyncio
class TestResourceAuditLogs:

    async def test_resource_audit_logs(
        self, test_client: AsyncClient, admin_access_token, test_audit_log
    ):
        response = await test_client.get(
            "/api/v1/audit-logs/resource/RecycledSIM/1",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    async def test_resource_id_validation_invalid_chars(
        self, test_client: AsyncClient, admin_access_token
    ):
        response = await test_client.get(
            "/api/v1/audit-logs/resource/User/../../etc/passwd",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [404, 422]

    async def test_resource_id_validation_sql_injection(
        self, test_client: AsyncClient, admin_access_token
    ):
        response = await test_client.get(
            "/api/v1/audit-logs/resource/User/1' OR '1'='1",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [400, 404, 422]


@pytest.mark.asyncio
class TestPaginationLimit:

    async def test_pagination_limit(
        self, test_client: AsyncClient, admin_access_token
    ):
        response = await test_client.get(
            "/api/v1/audit-logs?skip=0&limit=10",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10

    async def test_pagination_exceeds_max(
        self, test_client: AsyncClient, admin_access_token
    ):
        response = await test_client.get(
            "/api/v1/audit-logs?limit=200",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 422
