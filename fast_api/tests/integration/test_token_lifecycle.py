import pytest
from httpx import AsyncClient
from fast_api.auth.authlib.jwt_handler import JWTHandler


@pytest.mark.asyncio
class TestTokenLifecycle:

    async def test_full_login_refresh_logout_flow(
        self, test_client: AsyncClient, test_user
    ):
        login_resp = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
        assert login_resp.status_code == 200
        tokens = login_resp.json()

        refresh_resp = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh_resp.status_code == 200
        new_tokens = refresh_resp.json()

        logout_resp = await test_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
        )
        assert logout_resp.status_code == 200

    async def test_old_refresh_token_cannot_be_reused_after_rotation(
        self, test_client: AsyncClient, test_user
    ):
        login_resp = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
        assert login_resp.status_code == 200
        original_refresh = login_resp.json()["refresh_token"]

        rotate_resp = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": original_refresh},
        )
        assert rotate_resp.status_code == 200

        reuse_resp = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": original_refresh},
        )
        assert reuse_resp.status_code == 401

    async def test_new_refresh_token_works_after_rotation(
        self, test_client: AsyncClient, test_user
    ):
        login_resp = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
        original_refresh = login_resp.json()["refresh_token"]

        rotate_resp = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": original_refresh},
        )
        new_refresh = rotate_resp.json()["refresh_token"]

        second_rotate_resp = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": new_refresh},
        )
        assert second_rotate_resp.status_code == 200
