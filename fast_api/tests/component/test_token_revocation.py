import pytest
from httpx import AsyncClient
from fast_api.auth.authlib.jwt_handler import JWTHandler


@pytest.mark.asyncio
class TestTokenRevocationFlow:

    async def test_refresh_returns_new_tokens(
        self, test_client: AsyncClient, test_user
    ):
        refresh_token = JWTHandler.create_refresh_token(
            data={"sub": str(test_user.id), "email": test_user.email}
        )
        response = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != refresh_token

    async def test_reusing_old_refresh_token_after_rotation_is_rejected(
        self, test_client: AsyncClient, test_user
    ):
        refresh_token = JWTHandler.create_refresh_token(
            data={"sub": str(test_user.id), "email": test_user.email}
        )

        first_response = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert first_response.status_code == 200

        second_response = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert second_response.status_code == 401

    async def test_logout_succeeds(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

    async def test_refresh_with_invalid_token_rejected(
        self, test_client: AsyncClient
    ):
        response = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401
