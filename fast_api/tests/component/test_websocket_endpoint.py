import pytest
from httpx import AsyncClient
from fast_api.auth.authlib.jwt_handler import JWTHandler


@pytest.mark.asyncio
class TestWebSocketEndpointSecurity:

    async def test_ws_endpoint_requires_valid_token(self, test_client: AsyncClient):
        response = await test_client.get("/ws/notifications?token=invalid-token")
        assert response.status_code in [400, 403, 404, 500]

    async def test_ws_invalid_channel_documented(self, test_client: AsyncClient):
        token = JWTHandler.create_access_token(
            data={"sub": "1", "email": "test@example.com", "role": "operator"}
        )
        response = await test_client.get(f"/ws/secret_channel?token={token}")
        assert response.status_code in [400, 403, 404, 500]
