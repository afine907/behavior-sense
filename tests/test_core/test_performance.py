"""
性能工具测试
"""
import pytest
from behavior_core.performance import (
    LRUCache,
    BatchProcessor,
    RateLimiter,
    Timer,
)


class TestLRUCache:
    def test_set_get(self):
        cache = LRUCache(maxsize=10)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_eviction(self):
        cache = LRUCache(maxsize=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # evicts "a"
        assert cache.get("a") is None
        assert cache.get("c") == 3

    def test_ttl(self):
        import time
        cache = LRUCache(maxsize=10, ttl=0.1)
        cache.set("key", "value")
        assert cache.get("key") == "value"
        time.sleep(0.2)
        assert cache.get("key") is None

    def test_delete(self):
        cache = LRUCache()
        cache.set("key", "value")
        cache.delete("key")
        assert cache.get("key") is None

    def test_clear(self):
        cache = LRUCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.size == 0


class TestBatchProcessor:
    def test_add_below_batch_size(self):
        bp = BatchProcessor(batch_size=5)
        bp.add(1)
        bp.add(2)
        assert bp.pending == 2

    def test_flush_on_batch_size(self):
        flushed = []
        bp = BatchProcessor(batch_size=3)
        bp.set_flush_callback(lambda items: flushed.extend(items))

        bp.add(1)
        bp.add(2)
        bp.add(3)  # Triggers flush

        assert len(flushed) == 3
        assert bp.pending == 0

    def test_manual_flush(self):
        bp = BatchProcessor(batch_size=10)
        bp.add(1)
        bp.add(2)
        items = bp.flush()
        assert items == [1, 2]
        assert bp.pending == 0


class TestRateLimiter:
    def test_allow_within_limit(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert limiter.allow() is True

    def test_deny_over_limit(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        assert limiter.allow() is True
        assert limiter.allow() is True
        assert limiter.allow() is False

    def test_remaining(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        limiter.allow()
        limiter.allow()
        assert limiter.remaining == 3


class TestTimer:
    def test_sync_timer(self):
        import time
        with Timer("test") as t:
            time.sleep(0.1)
        assert t.elapsed_ms >= 100

    @pytest.mark.asyncio
    async def test_async_timer(self):
        import asyncio
        async with Timer("test") as t:
            await asyncio.sleep(0.1)
        assert t.elapsed_ms >= 100
