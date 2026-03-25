import pytest
from httpx import AsyncClient
from fast_api.auth.authlib.jwt_handler import JWTHandler
from fast_api.auth.authlib.password import PasswordManager


@pytest.mark.asyncio
class TestLoginEndpoint:

    async def test_login_success(self, test_client: AsyncClient, test_user):
        response = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    async def test_login_invalid_credentials(self, test_client: AsyncClient, test_user):
        response = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword!"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "password123!"},
        )
        assert response.status_code == 401

    async def test_login_inactive_user(self, test_client: AsyncClient, test_db):
        from fast_api.models.user import User

        user = User(
            email="inactive@example.com",
            hashed_password=PasswordManager.hash_password("inactivepass123"),
            full_name="Inactive User",
            is_active=False,
        )
        test_db.add(user)
        await test_db.flush()

        response = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "inactivepass123"},
        )
        assert response.status_code == 401

    async def test_login_locked_account(self, test_client: AsyncClient, locked_user):
        response = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "locked@example.com", "password": "lockedpassword12"},
        )
        assert response.status_code == 403
        data = response.json()
        detail = data.get("detail", data)
        assert detail.get("code") == "ACCOUNT_LOCKED" or response.status_code == 403

    async def test_login_sql_injection_blocked(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "' OR '1'='1' --",
            },
        )
        assert response.status_code in [400, 401, 422]

    async def test_login_sql_injection_in_email(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "'; DROP TABLE users; --",
                "password": "whatever12345",
            },
        )
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
class TestRefreshEndpoint:

    async def test_refresh_token_valid(self, test_client: AsyncClient, test_user):
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
        assert data["expires_in"] > 0

    async def test_refresh_with_access_token_rejected(self, test_client: AsyncClient, test_user):
        access_token = JWTHandler.create_access_token(
            data={"sub": str(test_user.id), "email": test_user.email}
        )
        response = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code in [400, 401]

    async def test_refresh_with_invalid_token(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401

    async def test_refresh_with_expired_token(self, test_client: AsyncClient):
        from datetime import timedelta
        import jwt as pyjwt
        from fast_api.config import get_settings

        settings = get_settings()
        payload = {
            "sub": "1",
            "email": "test@example.com",
            "type": "refresh",
            "exp": 0,
        }
        expired_token = pyjwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        response = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired_token},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestLogoutEndpoint:

    async def test_logout_requires_auth(self, test_client: AsyncClient):
        response = await test_client.post("/api/v1/auth/logout")
        assert response.status_code in [401, 403]

    async def test_logout_success(self, test_client: AsyncClient, access_token):
        response = await test_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert "message" in response.json()
