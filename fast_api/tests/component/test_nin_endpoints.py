import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestNINEndpoints:
    """Tests for NIN linkage endpoints."""

    async def test_verify_nin_linked(
        self, test_client: AsyncClient, access_token, test_nin_linkage
    ):
        """Test verifying NIN linkage."""
        response = await test_client.post(
            "/api/v1/nin-linkages/verify",
            json={"msisdn": "+2347012345678"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_linked"] is True
        assert data["nin"] == "12345678901"

    async def test_verify_nin_unlinked(
        self, test_client: AsyncClient, access_token
    ):
        """Test verifying unlinked NIN."""
        response = await test_client.post(
            "/api/v1/nin-linkages/verify",
            json={"msisdn": "+2349012345678"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_linked"] is False
        assert data["nin"] is None

    async def test_get_nin_linkages(
        self, test_client: AsyncClient, access_token, test_nin_linkage
    ):
        """Test getting all NIN linkages."""
        response = await test_client.get(
            "/api/v1/nin-linkages",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_bulk_check_nin_linkages(
        self, test_client: AsyncClient, access_token, test_nin_linkage
    ):
        """Test bulk checking NIN linkages."""
        response = await test_client.post(
            "/api/v1/nin-linkages/bulk-check",
            json={
                "msisdns": [
                    "+2347012345678",
                    "+2348012345678",
                    "+2349012345678",
                ]
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_checked"] == 3
        assert data["linked_count"] >= 1
        assert len(data["results"]) == 3

    async def test_unauthorized_verify_nin(self, test_client: AsyncClient):
        """Test verifying NIN without authentication."""
        response = await test_client.post(
            "/api/v1/nin-linkages/verify",
            json={"msisdn": "+2347012345678"},
        )
        assert response.status_code == 401
