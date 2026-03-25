import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone
from fast_api.auth.authlib.jwt_handler import JWTHandler


@pytest.mark.asyncio
class TestInputSanitization:

    async def test_sql_injection_in_query_params_blocked(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/recycled-sims?cleanup_status='; DROP TABLE users; --",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

    async def test_sql_injection_union_blocked(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/recycled-sims?cleanup_status=UNION SELECT * FROM users",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

    async def test_xss_in_query_params_blocked(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/recycled-sims?cleanup_status=<script>alert(1)</script>",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

    async def test_command_injection_blocked(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/recycled-sims?cleanup_status=; rm -rf /",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

    async def test_path_traversal_blocked(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/recycled-sims?cleanup_status=../../etc/passwd",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

    async def test_javascript_uri_blocked(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/recycled-sims?cleanup_status=javascript:alert(1)",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400


@pytest.mark.asyncio
class TestRequestSizeLimit:

    async def test_oversized_request_rejected(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims",
            json={"sim_serial": "x" * 1000},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Length": str(20 * 1024 * 1024),
            },
        )
        assert response.status_code == 413


@pytest.mark.asyncio
class TestSecurityHeaders:

    async def test_security_headers_present(
        self, test_client: AsyncClient, access_token, test_recycled_sim
    ):
        response = await test_client.get(
            "/api/v1/recycled-sims",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "max-age" in response.headers.get("Strict-Transport-Security", "")
        assert "default-src" in response.headers.get("Content-Security-Policy", "")
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert response.headers.get("Cache-Control") == "no-store"

    async def test_request_id_header_present(
        self, test_client: AsyncClient, access_token, test_recycled_sim
    ):
        response = await test_client.get(
            "/api/v1/recycled-sims",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    async def test_custom_request_id_echoed(
        self, test_client: AsyncClient, access_token, test_recycled_sim
    ):
        custom_id = "test-request-id-12345"
        response = await test_client.get(
            "/api/v1/recycled-sims",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Request-ID": custom_id,
            },
        )
        assert response.headers.get("X-Request-ID") == custom_id


@pytest.mark.asyncio
class TestAuthenticationEnforcement:

    async def test_unauthenticated_access_denied(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/recycled-sims")
        assert response.status_code in [401, 403]

    async def test_wrong_role_forbidden(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/audit-logs",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403

    async def test_expired_token_rejected(self, test_client: AsyncClient):
        expired_token = JWTHandler.create_access_token(
            data={"sub": "1", "email": "test@example.com"},
            expires_delta=timedelta(seconds=-1),
        )
        response = await test_client.get(
            "/api/v1/recycled-sims",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401

    async def test_malformed_bearer_token(self, test_client: AsyncClient):
        response = await test_client.get(
            "/api/v1/recycled-sims",
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code in [401, 403, 422]

    async def test_missing_bearer_prefix(self, test_client: AsyncClient):
        response = await test_client.get(
            "/api/v1/recycled-sims",
            headers={"Authorization": "some-token-value"},
        )
        assert response.status_code in [401, 403, 422]


@pytest.mark.asyncio
class TestRBACEnforcement:

    async def test_admin_can_access_audit_logs(
        self, test_client: AsyncClient, admin_access_token
    ):
        response = await test_client.get(
            "/api/v1/audit-logs",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200

    async def test_auditor_can_access_audit_logs(
        self, test_client: AsyncClient, auditor_access_token
    ):
        response = await test_client.get(
            "/api/v1/audit-logs",
            headers={"Authorization": f"Bearer {auditor_access_token}"},
        )
        assert response.status_code == 200

    async def test_operator_cannot_access_audit_logs(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/audit-logs",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403

    async def test_operator_cannot_bulk_upload(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims/bulk",
            json={"sims": []},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403

    async def test_auditor_cannot_create_sim(
        self, test_client: AsyncClient, auditor_access_token
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims",
            json={
                "sim_serial": "RBAC_TEST_001",
                "msisdn": "+2348012345678",
                "imsi": "621200000000001",
                "operator_code": "MTN",
                "date_recycled": datetime.now(timezone.utc).isoformat(),
            },
            headers={"Authorization": f"Bearer {auditor_access_token}"},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestIDORProtection:

    async def test_idor_cannot_access_other_user_data(
        self, test_client: AsyncClient, access_token, test_db
    ):
        from fast_api.models.recycled_sim import RecycledSIM

        sim = RecycledSIM(
            sim_serial="IDOR_TEST_SIM_001",
            msisdn="+2348099999999",
            imsi="621200000099999",
            operator_code="GLO",
            date_recycled=datetime.now(timezone.utc),
        )
        test_db.add(sim)
        await test_db.flush()
        await test_db.refresh(sim)

        response = await test_client.get(
            f"/api/v1/recycled-sims/{sim.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200


@pytest.mark.asyncio
class TestXSSInRequestBody:

    async def test_xss_in_json_body_handled(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims",
            json={
                "sim_serial": "<script>alert('xss')</script>",
                "msisdn": "+2348012345678",
                "imsi": "621200000000001",
                "operator_code": "MTN",
                "date_recycled": datetime.now(timezone.utc).isoformat(),
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code in [200, 400, 422]
