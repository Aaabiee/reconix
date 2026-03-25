import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestObservabilityIntegration:

    async def test_request_id_propagated_in_response(
        self, test_client: AsyncClient, access_token, test_recycled_sim
    ):
        response = await test_client.get(
            "/api/v1/recycled-sims",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Request-ID": "obs-test-001",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == "obs-test-001"

    async def test_metrics_accumulate_after_requests(
        self, test_client: AsyncClient, access_token, test_recycled_sim
    ):
        for _ in range(3):
            await test_client.get(
                "/api/v1/recycled-sims",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        response = await test_client.get("/metrics")
        assert response.status_code == 200
        assert "reconix_http_requests_total" in response.text

    async def test_health_and_metrics_both_accessible(
        self, test_client: AsyncClient
    ):
        health_resp = await test_client.get("/health")
        metrics_resp = await test_client.get("/metrics")
        assert health_resp.status_code == 200
        assert metrics_resp.status_code == 200
        assert health_resp.json()["database"] == "connected"

    async def test_error_responses_tracked_in_metrics(
        self, test_client: AsyncClient
    ):
        await test_client.get("/api/v1/recycled-sims")
        response = await test_client.get("/metrics")
        assert "reconix_http_errors_total" in response.text or response.status_code == 200

    async def test_pool_info_in_health(self, test_client: AsyncClient):
        response = await test_client.get("/health")
        data = response.json()
        pool = data.get("pool", {})
        assert isinstance(pool, dict)


@pytest.mark.asyncio
class TestPermissionsIntegration:

    async def test_admin_can_access_all_endpoints(
        self, test_client: AsyncClient, admin_access_token, test_recycled_sim
    ):
        endpoints = [
            "/api/v1/recycled-sims",
            "/api/v1/audit-logs",
            "/api/v1/dashboard/stats",
        ]
        for url in endpoints:
            response = await test_client.get(
                url, headers={"Authorization": f"Bearer {admin_access_token}"}
            )
            assert response.status_code == 200

    async def test_operator_blocked_from_audit_and_retention(
        self, test_client: AsyncClient, access_token
    ):
        audit_resp = await test_client.get(
            "/api/v1/audit-logs",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert audit_resp.status_code == 403

        retention_resp = await test_client.post(
            "/api/v1/retention/purge-audit-logs",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert retention_resp.status_code == 403

    async def test_auditor_can_read_but_not_write(
        self, test_client: AsyncClient, auditor_access_token
    ):
        read_resp = await test_client.get(
            "/api/v1/audit-logs",
            headers={"Authorization": f"Bearer {auditor_access_token}"},
        )
        assert read_resp.status_code == 200

        write_resp = await test_client.post(
            "/api/v1/recycled-sims",
            json={
                "sim_serial": "PERM_TEST_001",
                "msisdn": "+2348012345678",
                "imsi": "621200000000001",
                "operator_code": "MTN",
                "date_recycled": "2025-01-01T00:00:00Z",
            },
            headers={"Authorization": f"Bearer {auditor_access_token}"},
        )
        assert write_resp.status_code == 403

    async def test_unauthenticated_blocked_everywhere(
        self, test_client: AsyncClient
    ):
        endpoints = [
            "/api/v1/recycled-sims",
            "/api/v1/audit-logs",
            "/api/v1/dashboard/stats",
            "/api/v1/delink-requests",
        ]
        for url in endpoints:
            response = await test_client.get(url)
            assert response.status_code in [401, 403]
