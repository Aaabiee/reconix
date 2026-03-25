import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from fast_api.models.audit_log import AuditLog


@pytest.mark.asyncio
class TestRetentionEndpoint:

    async def test_purge_requires_admin(self, test_client: AsyncClient, access_token):
        response = await test_client.post(
            "/api/v1/retention/purge-audit-logs",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403

    async def test_purge_allowed_for_admin(self, test_client: AsyncClient, admin_access_token):
        response = await test_client.post(
            "/api/v1/retention/purge-audit-logs",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data
        assert "retention_days" in data

    async def test_purge_deletes_old_logs(self, test_client: AsyncClient, admin_access_token, test_db):
        old_log = AuditLog(
            action="test_action",
            resource_type="TestResource",
            resource_id="1",
            created_at=datetime.now(timezone.utc) - timedelta(days=400),
        )
        test_db.add(old_log)
        await test_db.flush()

        response = await test_client.post(
            "/api/v1/retention/purge-audit-logs",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] >= 1

    async def test_purge_auditor_forbidden(self, test_client: AsyncClient, auditor_access_token):
        response = await test_client.post(
            "/api/v1/retention/purge-audit-logs",
            headers={"Authorization": f"Bearer {auditor_access_token}"},
        )
        assert response.status_code == 403
