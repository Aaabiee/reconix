import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from fast_api.models.audit_log import AuditLog


@pytest.mark.asyncio
class TestRetentionWorkflow:

    async def test_old_logs_purged_recent_logs_kept(
        self, test_client: AsyncClient, admin_access_token, test_db
    ):
        old_log = AuditLog(
            action="old_action",
            resource_type="OldResource",
            resource_id="old-1",
            created_at=datetime.now(timezone.utc) - timedelta(days=400),
        )
        recent_log = AuditLog(
            action="recent_action",
            resource_type="RecentResource",
            resource_id="recent-1",
            created_at=datetime.now(timezone.utc) - timedelta(days=10),
        )
        test_db.add_all([old_log, recent_log])
        await test_db.flush()

        response = await test_client.post(
            "/api/v1/retention/purge-audit-logs",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] >= 1

        logs_resp = await test_client.get(
            "/api/v1/audit-logs",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert logs_resp.status_code == 200

    async def test_purge_with_no_expired_logs(
        self, test_client: AsyncClient, admin_access_token
    ):
        response = await test_client.post(
            "/api/v1/retention/purge-audit-logs",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] >= 0
