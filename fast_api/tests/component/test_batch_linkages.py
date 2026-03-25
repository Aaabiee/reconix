import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from fast_api.models.nin_linkage import NINLinkage
from fast_api.models.bvn_linkage import BVNLinkage


@pytest.mark.asyncio
class TestNINBatchBulkCheck:

    async def test_bulk_check_returns_results(
        self, test_client: AsyncClient, access_token, test_nin_linkage
    ):
        response = await test_client.post(
            "/api/v1/nin-linkages/bulk-check",
            json={"msisdns": ["+2347012345678", "+2348099999999"]},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_checked"] == 2
        assert data["linked_count"] == 1
        assert data["unlinked_count"] == 1

    async def test_bulk_check_empty_list(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/nin-linkages/bulk-check",
            json={"msisdns": []},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_checked"] == 0

    async def test_bulk_check_multiple_linked(
        self, test_client: AsyncClient, access_token, test_db
    ):
        linkage1 = NINLinkage(
            msisdn="+2348011111111",
            nin="11111111111",
            linked_date=datetime.now(timezone.utc),
            is_active=True,
            source="nimc_api",
            verified_at=datetime.now(timezone.utc),
        )
        linkage2 = NINLinkage(
            msisdn="+2348022222222",
            nin="22222222222",
            linked_date=datetime.now(timezone.utc),
            is_active=True,
            source="nimc_api",
            verified_at=datetime.now(timezone.utc),
        )
        test_db.add_all([linkage1, linkage2])
        await test_db.flush()

        response = await test_client.post(
            "/api/v1/nin-linkages/bulk-check",
            json={"msisdns": ["+2348011111111", "+2348022222222", "+2348033333333"]},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["linked_count"] == 2
        assert data["unlinked_count"] == 1

    async def test_bulk_check_requires_auth(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/v1/nin-linkages/bulk-check",
            json={"msisdns": ["+2347012345678"]},
        )
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestBVNBatchBulkCheck:

    async def test_bulk_check_returns_results(
        self, test_client: AsyncClient, access_token, test_bvn_linkage
    ):
        response = await test_client.post(
            "/api/v1/bvn-linkages/bulk-check",
            json={"msisdns": ["+2347012345678", "+2348099999999"]},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_checked"] == 2
        assert data["linked_count"] == 1
        assert data["unlinked_count"] == 1

    async def test_bulk_check_empty_list(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/bvn-linkages/bulk-check",
            json={"msisdns": []},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_checked"] == 0

    async def test_bulk_check_multiple_linked(
        self, test_client: AsyncClient, access_token, test_db
    ):
        linkage1 = BVNLinkage(
            msisdn="+2348044444444",
            bvn="44444444444",
            linked_date=datetime.now(timezone.utc),
            is_active=True,
            bank_code="011",
            source="nibss_api",
            verified_at=datetime.now(timezone.utc),
        )
        linkage2 = BVNLinkage(
            msisdn="+2348055555555",
            bvn="55555555555",
            linked_date=datetime.now(timezone.utc),
            is_active=True,
            bank_code="044",
            source="nibss_api",
            verified_at=datetime.now(timezone.utc),
        )
        test_db.add_all([linkage1, linkage2])
        await test_db.flush()

        response = await test_client.post(
            "/api/v1/bvn-linkages/bulk-check",
            json={"msisdns": ["+2348044444444", "+2348055555555", "+2348066666666"]},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["linked_count"] == 2
        assert data["unlinked_count"] == 1
