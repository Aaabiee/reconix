import pytest
from fast_api.db import (
    DatabaseEngineFactory,
    get_read_engine,
    get_read_session_factory,
    reset_engine,
)


class TestReadReplicaConfiguration:

    def test_get_read_engine_returns_none_without_config(self, monkeypatch):
        reset_engine()
        monkeypatch.setenv("DATABASE_READ_REPLICA_URL", "")
        from fast_api.config import get_settings
        get_settings.cache_clear()

        engine = get_read_engine()
        assert engine is None
        reset_engine()
        get_settings.cache_clear()

    def test_get_read_session_factory_returns_none_without_config(self, monkeypatch):
        reset_engine()
        monkeypatch.setenv("DATABASE_READ_REPLICA_URL", "")
        from fast_api.config import get_settings
        get_settings.cache_clear()

        factory = get_read_session_factory()
        assert factory is None
        reset_engine()
        get_settings.cache_clear()

    def test_database_engine_factory_rejects_unknown_driver(self):
        with pytest.raises(ValueError, match="Unsupported database driver"):
            DatabaseEngineFactory.create_engine(
                database_url="unknown://localhost/db",
                driver="nosql",
            )
