import time
import pytest
from fast_api.middleware.deduplication import DeduplicationCache, DEDUP_WINDOW_SECONDS


class TestDeduplicationCache:

    def setup_method(self):
        cache = DeduplicationCache()
        cache.reset()

    def test_singleton_instance(self):
        c1 = DeduplicationCache()
        c2 = DeduplicationCache()
        assert c1 is c2

    def test_first_request_not_duplicate(self):
        cache = DeduplicationCache()
        assert cache.is_duplicate("key-1") is False

    def test_second_request_is_duplicate(self):
        cache = DeduplicationCache()
        cache.is_duplicate("key-2")
        assert cache.is_duplicate("key-2") is True

    def test_different_keys_not_duplicate(self):
        cache = DeduplicationCache()
        cache.is_duplicate("key-a")
        assert cache.is_duplicate("key-b") is False

    def test_reset_clears_cache(self):
        cache = DeduplicationCache()
        cache.is_duplicate("key-reset")
        cache.reset()
        assert cache.is_duplicate("key-reset") is False

    def test_expired_entries_are_evicted(self):
        cache = DeduplicationCache()
        cache.is_duplicate("key-expire")

        with cache._data_lock:
            cache._cache["key-expire"] = time.monotonic() - DEDUP_WINDOW_SECONDS - 1

        assert cache.is_duplicate("key-expire") is False
