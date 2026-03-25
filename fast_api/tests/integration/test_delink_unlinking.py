import pytest
from httpx import AsyncClient
from datetime import datetime, timezone


@pytest.mark.asyncio
class TestDelinkActuallyUnlinks:

    async def test_complete_delink_unlinks_nin(
        self, test_db, test_recycled_sim, test_nin_linkage, test_user
    ):
        from fast_api.services.delink_service import DelinkService
        from fast_api.services.linkage_service import NINLinkageService
        from fast_api.models.delink_request import DelinkRequestType

        service = DelinkService(test_db)
        delink = await service.create_delink_request(
            recycled_sim_id=test_recycled_sim.id,
            request_type=DelinkRequestType.NIN,
            initiated_by=test_user.id,
            reason="Test NIN unlink",
        )

        await service.approve_delink_request(delink.id, test_user.id)
        await service.complete_delink_request(delink.id)

        nin_service = NINLinkageService(test_db)
        linkage = await nin_service.get_active_linkage_for_msisdn(test_recycled_sim.msisdn)
        assert linkage is None

    async def test_complete_delink_unlinks_bvn(
        self, test_db, test_recycled_sim, test_bvn_linkage, test_user
    ):
        from fast_api.services.delink_service import DelinkService
        from fast_api.services.linkage_service import BVNLinkageService
        from fast_api.models.delink_request import DelinkRequestType

        service = DelinkService(test_db)
        delink = await service.create_delink_request(
            recycled_sim_id=test_recycled_sim.id,
            request_type=DelinkRequestType.BVN,
            initiated_by=test_user.id,
            reason="Test BVN unlink",
        )

        await service.approve_delink_request(delink.id, test_user.id)
        await service.complete_delink_request(delink.id)

        bvn_service = BVNLinkageService(test_db)
        linkage = await bvn_service.get_active_linkage_for_msisdn(test_recycled_sim.msisdn)
        assert linkage is None

    async def test_complete_delink_creates_notifications(
        self, test_db, test_recycled_sim, test_nin_linkage, test_user
    ):
        from fast_api.services.delink_service import DelinkService
        from fast_api.models.delink_request import DelinkRequestType
        from fast_api.models.notification import Notification
        from sqlalchemy import select, func

        service = DelinkService(test_db)
        delink = await service.create_delink_request(
            recycled_sim_id=test_recycled_sim.id,
            request_type=DelinkRequestType.NIN,
            initiated_by=test_user.id,
        )
        await service.approve_delink_request(delink.id, test_user.id)
        await service.complete_delink_request(delink.id)

        count_result = await test_db.execute(
            select(func.count(Notification.id)).where(
                Notification.delink_request_id == delink.id
            )
        )
        notification_count = count_result.scalar()
        assert notification_count >= 3

    async def test_complete_delink_updates_sim_flags(
        self, test_db, test_recycled_sim, test_nin_linkage, test_bvn_linkage, test_user
    ):
        from fast_api.services.delink_service import DelinkService
        from fast_api.services.recycled_sim_service import RecycledSIMService
        from fast_api.models.delink_request import DelinkRequestType

        service = DelinkService(test_db)
        delink = await service.create_delink_request(
            recycled_sim_id=test_recycled_sim.id,
            request_type=DelinkRequestType.BOTH,
            initiated_by=test_user.id,
        )
        await service.approve_delink_request(delink.id, test_user.id)
        await service.complete_delink_request(delink.id)

        sim_service = RecycledSIMService(test_db)
        sim = await sim_service.get_sim_by_id(test_recycled_sim.id)
        assert sim.previous_nin_linked is False
        assert sim.previous_bvn_linked is False
        assert sim.cleanup_status == "completed"


@pytest.mark.asyncio
class TestMSISDNStatusEndpoint:

    async def test_status_returns_conflicted_for_linked_recycled_sim(
        self, test_client: AsyncClient, access_token, test_recycled_sim, test_nin_linkage
    ):
        response = await test_client.get(
            f"/api/v1/identity/msisdn/{test_recycled_sim.msisdn}/status",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CONFLICTED"
        assert data["is_recycled"] is True
        assert data["active_nin_linkages"] >= 1
        assert data["can_assign_to_new_user"] is False

    async def test_status_returns_available_for_unknown_msisdn(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.get(
            "/api/v1/identity/msisdn/+2349099999999/status",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "AVAILABLE"
        assert data["can_assign_to_new_user"] is True

    async def test_linkages_returns_history(
        self, test_client: AsyncClient, access_token, test_recycled_sim, test_nin_linkage
    ):
        response = await test_client.get(
            f"/api/v1/identity/msisdn/{test_recycled_sim.msisdn}/linkages",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_nin"] >= 1
        assert data["active_nin"] >= 1
        assert len(data["nin_linkages"]) >= 1


@pytest.mark.asyncio
class TestDetectionScan:

    async def test_detect_flags_conflicted_sims(
        self, test_client: AsyncClient, admin_access_token, test_recycled_sim, test_nin_linkage
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims/detect",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Detection scan completed"
        assert data["total_scanned"] >= 1
        assert data["conflicted"] >= 1

    async def test_detect_requires_admin(
        self, test_client: AsyncClient, access_token
    ):
        response = await test_client.post(
            "/api/v1/recycled-sims/detect",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403
