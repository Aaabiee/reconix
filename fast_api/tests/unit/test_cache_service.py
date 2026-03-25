import pytest
import asyncio
from fast_api.services.cache_service import CacheService


@pytest.fixture
def cache():
    return CacheService(redis_url="", prefix="test")


class TestCacheServiceFallback:

    @pytest.mark.asyncio
    async def test_connect_without_redis_returns_false(self, cache):
        result = await cache.connect()
        assert result is False

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        await cache.set("user:1", {"name": "Test", "role": "admin"}, ttl_seconds=60)
        result = await cache.get("user:1")
        assert result == {"name": "Test", "role": "admin"}

    @pytest.mark.asyncio
    async def test_get_missing_key_returns_none(self, cache):
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_key(self, cache):
        await cache.set("temp", "value", ttl_seconds=60)
        assert await cache.get("temp") == "value"
        await cache.delete("temp")
        assert await cache.get("temp") is None

    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, cache):
        await cache.set("sim:1", "data1", ttl_seconds=60)
        await cache.set("sim:2", "data2", ttl_seconds=60)
        await cache.set("user:1", "user_data", ttl_seconds=60)

        count = await cache.invalidate_pattern("sim:*")
        assert count == 2
        assert await cache.get("sim:1") is None
        assert await cache.get("user:1") == "user_data"

    @pytest.mark.asyncio
    async def test_blacklist_operations(self, cache):
        await cache.add_to_blacklist("jti_123", ttl_seconds=60)
        assert await cache.is_blacklisted("jti_123") is True
        assert await cache.is_blacklisted("jti_999") is False

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        key1 = CacheService.cache_key("user", "42", "profile")
        key2 = CacheService.cache_key("user", "42", "profile")
        key3 = CacheService.cache_key("user", "43", "profile")
        assert key1 == key2
        assert key1 != key3
        assert len(key1) == 32

    @pytest.mark.asyncio
    async def test_close_without_connection(self, cache):
        await cache.close()

    @pytest.mark.asyncio
    async def test_set_complex_value(self, cache):
        data = {
            "items": [1, 2, 3],
            "nested": {"key": "value"},
            "count": 42,
        }
        await cache.set("complex", data, ttl_seconds=60)
        result = await cache.get("complex")
        assert result == data

    @pytest.mark.asyncio
    async def test_prefix_isolation(self):
        cache_a = CacheService(redis_url="", prefix="app_a")
        cache_b = CacheService(redis_url="", prefix="app_b")

        await cache_a.set("shared_key", "value_a", ttl_seconds=60)
        await cache_b.set("shared_key", "value_b", ttl_seconds=60)

        assert await cache_a.get("shared_key") == "value_a"
        assert await cache_b.get("shared_key") == "value_b"
