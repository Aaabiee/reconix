import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from fast_api.models.recycled_sim import RecycledSIM
from fast_api.models.delink_request import DelinkRequest, DelinkRequestStatus


@pytest.mark.asyncio
class TestFullDelinkLifecycle:

    async def test_full_delink_lifecycle(
        self, test_client: AsyncClient, admin_access_token, access_token, test_db
    ):
        sim = RecycledSIM(
            sim_serial="LIFECYCLE_SIM_001",
            msisdn="+2347011111111",
            imsi="621234500000001",
            operator_code="MTN",
            date_recycled=datetime.now(timezone.utc),
            previous_nin_linked=True,
            previous_bvn_linked=True,
        )
        test_db.add(sim)
        await test_db.flush()
        await test_db.refresh(sim)

        create_resp = await test_client.post(
            "/api/v1/delink-requests",
            json={
                "recycled_sim_id": sim.id,
                "request_type": "both",
                "reason": "Full lifecycle test",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert create_resp.status_code == 200
        request_id = create_resp.json()["id"]
        assert create_resp.json()["status"] == "pending"

        get_resp = await test_client.get(
            f"/api/v1/delink-requests/{request_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "pending"

        approve_resp = await test_client.post(
            f"/api/v1/delink-requests/{request_id}/approve",
            json={"approved": True},
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "processing"
        assert approve_resp.json()["approved_by"] is not None

        final_resp = await test_client.get(
            f"/api/v1/delink-requests/{request_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert final_resp.status_code == 200
        assert final_resp.json()["status"] == "processing"


@pytest.mark.asyncio
class TestDelinkCancellationFlow:

    async def test_delink_cancellation_flow(
        self, test_client: AsyncClient, access_token, test_db
    ):
        sim = RecycledSIM(
            sim_serial="CANCEL_SIM_001",
            msisdn="+2347022222222",
            imsi="621234500000002",
            operator_code="GLO",
            date_recycled=datetime.now(timezone.utc),
        )
        test_db.add(sim)
        await test_db.flush()
        await test_db.refresh(sim)

        create_resp = await test_client.post(
            "/api/v1/delink-requests",
            json={
                "recycled_sim_id": sim.id,
                "request_type": "nin",
                "reason": "Cancellation test",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert create_resp.status_code == 200
        request_id = create_resp.json()["id"]
        assert create_resp.json()["status"] == "pending"

        cancel_resp = await test_client.post(
            f"/api/v1/delink-requests/{request_id}/cancel",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelled"

        get_resp = await test_client.get(
            f"/api/v1/delink-requests/{request_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "cancelled"

    async def test_cannot_cancel_already_cancelled(
        self, test_client: AsyncClient, access_token, test_db
    ):
        sim = RecycledSIM(
            sim_serial="CANCEL_SIM_002",
            msisdn="+2347033333333",
            imsi="621234500000003",
            operator_code="9MOBILE",
            date_recycled=datetime.now(timezone.utc),
        )
        test_db.add(sim)
        await test_db.flush()
        await test_db.refresh(sim)

        req = DelinkRequest(
            recycled_sim_id=sim.id,
            request_type="bvn",
            status=DelinkRequestStatus.CANCELLED,
            initiated_by=1,
        )
        test_db.add(req)
        await test_db.flush()
        await test_db.refresh(req)

        cancel_resp = await test_client.post(
            f"/api/v1/delink-requests/{req.id}/cancel",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert cancel_resp.status_code == 422


@pytest.mark.asyncio
class TestDelinkFailureFlow:

    async def test_delink_failure_flow(
        self, test_client: AsyncClient, admin_access_token, access_token, test_db
    ):
        sim = RecycledSIM(
            sim_serial="FAIL_SIM_001",
            msisdn="+2347044444444",
            imsi="621234500000004",
            operator_code="AIRTEL",
            date_recycled=datetime.now(timezone.utc),
        )
        test_db.add(sim)
        await test_db.flush()
        await test_db.refresh(sim)

        create_resp = await test_client.post(
            "/api/v1/delink-requests",
            json={
                "recycled_sim_id": sim.id,
                "request_type": "both",
                "reason": "Failure test",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert create_resp.status_code == 200
        request_id = create_resp.json()["id"]

        approve_resp = await test_client.post(
            f"/api/v1/delink-requests/{request_id}/approve",
            json={"approved": True},
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "processing"


@pytest.mark.asyncio
class TestDelinkMultipleRequests:

    async def test_multiple_delink_requests_for_same_sim(
        self, test_client: AsyncClient, access_token, test_db
    ):
        sim = RecycledSIM(
            sim_serial="MULTI_SIM_001",
            msisdn="+2347055555555",
            imsi="621234500000005",
            operator_code="MTN",
            date_recycled=datetime.now(timezone.utc),
        )
        test_db.add(sim)
        await test_db.flush()
        await test_db.refresh(sim)

        resp1 = await test_client.post(
            "/api/v1/delink-requests",
            json={
                "recycled_sim_id": sim.id,
                "request_type": "nin",
                "reason": "First request",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp1.status_code == 200

        resp2 = await test_client.post(
            "/api/v1/delink-requests",
            json={
                "recycled_sim_id": sim.id,
                "request_type": "bvn",
                "reason": "Second request",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp2.status_code == 200

        assert resp1.json()["id"] != resp2.json()["id"]
        assert resp1.json()["request_type"] == "nin"
        assert resp2.json()["request_type"] == "bvn"
