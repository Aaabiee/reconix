import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_DRIVER"] = "sqlite"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-at-least-32-chars"
os.environ["ENVIRONMENT"] = "testing"
os.environ["FIELD_ENCRYPTION_KEY"] = "test-encryption-key-for-testing-only-32chars-min"
os.environ["ENABLE_JSON_LOGGING"] = "false"
os.environ["ENABLE_IDEMPOTENCY"] = "false"

import pytest
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from fast_api.db import Base, set_engine, reset_engine, get_db
from fast_api.auth.authlib.jwt_handler import JWTHandler
from fast_api.auth.authlib.password import PasswordManager
from fast_api.models.user import User, UserRole
from fast_api.models.recycled_sim import RecycledSIM, CleanupStatus
from fast_api.models.nin_linkage import NINLinkage
from fast_api.models.bvn_linkage import BVNLinkage
from fast_api.models.delink_request import DelinkRequest, DelinkRequestStatus, DelinkRequestType
from fast_api.models.notification import Notification, NotificationStatus
from fast_api.models.audit_log import AuditLog
from fast_api.models.idempotency_key import IdempotencyKey
from fast_api.models.revoked_token import RevokedToken
from fast_api.models.stakeholder import Stakeholder

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"



@pytest.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine):
    set_engine(test_engine)
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()
        await session.close()
    reset_engine()


@pytest.fixture
async def test_client(test_engine):
    set_engine(test_engine)

    from fast_api.main import app

    async def override_get_db():
        async_session = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    from fast_api.db import get_read_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_read_db] = override_get_db
    app.state.ready = True

    from fast_api.middleware.rate_limiter import limiter
    try:
        limiter.reset()
    except Exception:
        pass

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    reset_engine()


@pytest.fixture
async def test_user(test_db):
    user = User(
        email="test@example.com",
        hashed_password=PasswordManager.hash_password("testpassword123"),
        full_name="Test User",
        role="operator",
        organization="Test Org",
        is_active=True,
    )
    test_db.add(user)
    await test_db.flush()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def test_admin(test_db):
    user = User(
        email="admin@example.com",
        hashed_password=PasswordManager.hash_password("adminpassword123"),
        full_name="Admin User",
        role="admin",
        organization="Admin Org",
        is_active=True,
    )
    test_db.add(user)
    await test_db.flush()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def test_auditor(test_db):
    user = User(
        email="auditor@example.com",
        hashed_password=PasswordManager.hash_password("auditorpassword1"),
        full_name="Auditor User",
        role="auditor",
        organization="Audit Org",
        is_active=True,
    )
    test_db.add(user)
    await test_db.flush()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def locked_user(test_db):
    from datetime import timedelta
    user = User(
        email="locked@example.com",
        hashed_password=PasswordManager.hash_password("lockedpassword12"),
        full_name="Locked User",
        role="operator",
        organization="Test Org",
        is_active=True,
        failed_login_attempts=5,
        locked_until=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    test_db.add(user)
    await test_db.flush()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def access_token(test_user):
    return JWTHandler.create_access_token(
        data={
            "sub": str(test_user.id),
            "email": test_user.email,
            "role": test_user.role,
        }
    )


@pytest.fixture
async def admin_access_token(test_admin):
    return JWTHandler.create_access_token(
        data={
            "sub": str(test_admin.id),
            "email": test_admin.email,
            "role": test_admin.role,
        }
    )


@pytest.fixture
async def auditor_access_token(test_auditor):
    return JWTHandler.create_access_token(
        data={
            "sub": str(test_auditor.id),
            "email": test_auditor.email,
            "role": test_auditor.role,
        }
    )


@pytest.fixture
async def test_recycled_sim(test_db):
    sim = RecycledSIM(
        sim_serial="89234567890123456789",
        msisdn="+2347012345678",
        imsi="621234567890123",
        operator_code="MTN",
        date_recycled=datetime.now(timezone.utc),
        previous_owner_nin="12345678901",
        previous_nin_linked=True,
        previous_bvn_linked=True,
    )
    test_db.add(sim)
    await test_db.flush()
    await test_db.refresh(sim)
    return sim


@pytest.fixture
async def test_nin_linkage(test_db):
    linkage = NINLinkage(
        msisdn="+2347012345678",
        nin="12345678901",
        linked_date=datetime.now(timezone.utc),
        is_active=True,
        source="nimc_api",
        verified_at=datetime.now(timezone.utc),
    )
    test_db.add(linkage)
    await test_db.flush()
    await test_db.refresh(linkage)
    return linkage


@pytest.fixture
async def test_bvn_linkage(test_db):
    linkage = BVNLinkage(
        msisdn="+2347012345678",
        bvn="12345678901",
        linked_date=datetime.now(timezone.utc),
        is_active=True,
        bank_code="007",
        source="nibss_api",
        verified_at=datetime.now(timezone.utc),
    )
    test_db.add(linkage)
    await test_db.flush()
    await test_db.refresh(linkage)
    return linkage


@pytest.fixture
async def test_delink_request(test_db, test_recycled_sim, test_user):
    request = DelinkRequest(
        recycled_sim_id=test_recycled_sim.id,
        request_type="both",
        status="pending",
        initiated_by=test_user.id,
        reason="Test delink",
    )
    test_db.add(request)
    await test_db.flush()
    await test_db.refresh(request)
    return request


@pytest.fixture
async def test_notification(test_db, test_delink_request):
    notification = Notification(
        delink_request_id=test_delink_request.id,
        recipient_type="former_owner",
        channel="email",
        recipient_address="user@example.com",
        status="pending",
        message_template="delink_notice",
    )
    test_db.add(notification)
    await test_db.flush()
    await test_db.refresh(notification)
    return notification


@pytest.fixture
async def test_audit_log(test_db, test_user):
    log = AuditLog(
        user_id=test_user.id,
        action="create",
        resource_type="RecycledSIM",
        resource_id="1",
        new_value={"msisdn": "+2347012345678"},
        ip_address="127.0.0.1",
        user_agent="test-client",
    )
    test_db.add(log)
    await test_db.flush()
    await test_db.refresh(log)
    return log
