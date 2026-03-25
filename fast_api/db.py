from __future__ import annotations

from typing import TypeVar, Generic, Any
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import select, update, delete, func

Base = declarative_base()

_engine: AsyncEngine | None = None
_read_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker | None = None
_read_session_factory: async_sessionmaker | None = None


class DatabaseEngineFactory:

    @staticmethod
    def create_engine(
        database_url: str,
        driver: str,
        pool_size: int = 20,
        max_overflow: int = 20,
        echo: bool = False,
    ) -> AsyncEngine:
        driver = driver.lower().strip()

        if driver == "postgresql":
            if "postgresql+" not in database_url:
                database_url = database_url.replace(
                    "postgresql://", "postgresql+asyncpg://"
                )
        elif driver == "mysql":
            if "mysql+" not in database_url:
                database_url = database_url.replace("mysql://", "mysql+aiomysql://")
        elif driver == "oracle":
            if "oracle+" not in database_url:
                database_url = database_url.replace("oracle://", "oracle+oracledb://")
        elif driver == "intersystems":
            if "intersystems+" not in database_url:
                database_url = database_url.replace(
                    "intersystems://", "intersystems+pyodbc://"
                )
        elif driver == "sqlite":
            pass
        else:
            raise ValueError(
                f"Unsupported database driver: {driver}. "
                f"Supported: postgresql, mysql, oracle, intersystems, sqlite"
            )

        connect_args = {}
        if "sqlite" in database_url:
            connect_args = {"timeout": 30, "check_same_thread": False}
            return create_async_engine(
                database_url,
                echo=echo,
                connect_args=connect_args,
            )
        elif "postgresql" in database_url:
            connect_args = {"command_timeout": 30}

        return create_async_engine(
            database_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args=connect_args,
        )


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        from fast_api.config import get_settings

        settings = get_settings()
        _engine = DatabaseEngineFactory.create_engine(
            database_url=settings.DATABASE_URL,
            driver=settings.DATABASE_DRIVER,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            echo=settings.DATABASE_ECHO_SQL,
        )
    return _engine


def get_read_engine() -> AsyncEngine | None:
    global _read_engine
    if _read_engine is None:
        from fast_api.config import get_settings

        settings = get_settings()
        read_url = getattr(settings, "DATABASE_READ_REPLICA_URL", "")
        if not read_url:
            return None

        _read_engine = DatabaseEngineFactory.create_engine(
            database_url=read_url,
            driver=settings.DATABASE_DRIVER,
            pool_size=max(settings.DATABASE_POOL_SIZE // 2, 5),
            max_overflow=max(settings.DATABASE_MAX_OVERFLOW // 2, 5),
            echo=settings.DATABASE_ECHO_SQL,
        )
    return _read_engine


def get_session_factory() -> async_sessionmaker:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


def get_read_session_factory() -> async_sessionmaker | None:
    global _read_session_factory
    if _read_session_factory is None:
        engine = get_read_engine()
        if engine is None:
            return None
        _read_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _read_session_factory


def set_engine(engine: AsyncEngine) -> None:
    global _engine, _session_factory
    _engine = engine
    _session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


def reset_engine() -> None:
    global _engine, _read_engine, _session_factory, _read_session_factory
    _engine = None
    _read_engine = None
    _session_factory = None
    _read_session_factory = None


async def get_read_db() -> AsyncSession:
    read_factory = get_read_session_factory()
    if read_factory is None:
        async for session in get_db():
            yield session
        return

    async with read_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db() -> AsyncSession:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    engine = get_engine()
    await engine.dispose()


T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):

    def __init__(self, db: AsyncSession, model: type[T]):
        self.db = db
        self.model = model

    async def create(self, obj_in: dict[str, Any]) -> T:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_by_id(self, id: Any) -> T | None:
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> list[T]:
        stmt = select(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    stmt = stmt.where(getattr(self.model, key) == value)

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update(self, id: Any, obj_in: dict[str, Any]) -> T | None:
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return None

        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: Any) -> bool:
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return False

        await self.db.delete(db_obj)
        await self.db.flush()
        return True

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        stmt = select(func.count(self.model.id))

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    stmt = stmt.where(getattr(self.model, key) == value)

        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def exists(self, **filters) -> bool:
        stmt = select(func.count(self.model.id))

        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)

        result = await self.db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    async def delete_by_filter(self, **filters) -> int:
        stmt = delete(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)

        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount or 0
