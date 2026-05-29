"""
性能优化工具
"""
import asyncio
import functools
import hashlib
import json
import time
from collections import OrderedDict
from datetime import UTC, datetime
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class LRUCache:
    """LRU缓存"""

    def __init__(self, maxsize: int = 1000, ttl: float = 300.0):
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def get(self, key: str) -> Any | None:
        """获取缓存"""
        if key in self._cache:
            value, expires_at = self._cache[key]
            if time.time() < expires_at:
                self._cache.move_to_end(key)
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """设置缓存"""
        if key in self._cache:
            del self._cache[key]
        elif len(self._cache) >= self.maxsize:
            self._cache.popitem(last=False)
        self._cache[key] = (value, time.time() + self.ttl)

    def delete(self, key: str) -> None:
        """删除缓存"""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        """命中率"""
        return 0.0  # TODO: Track hits/misses


class BatchProcessor:
    """批量处理器"""

    def __init__(self, batch_size: int = 100, flush_interval: float = 5.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._buffer: list[Any] = []
        self._last_flush = time.time()
        self._flush_callback: Callable | None = None

    def set_flush_callback(self, callback: Callable) -> None:
        """设置刷新回调"""
        self._flush_callback = callback

    def add(self, item: Any) -> bool:
        """添加项目，返回是否触发刷新"""
        self._buffer.append(item)

        if len(self._buffer) >= self.batch_size:
            self.flush()
            return True

        if time.time() - self._last_flush >= self.flush_interval:
            self.flush()
            return True

        return False

    def flush(self) -> list[Any]:
        """刷新缓冲区"""
        if not self._buffer:
            return []

        items = self._buffer.copy()
        self._buffer.clear()
        self._last_flush = time.time()

        if self._flush_callback:
            self._flush_callback(items)

        return items

    @property
    def pending(self) -> int:
        return len(self._buffer)


def memoize(ttl: float = 60.0, maxsize: int = 128):
    """记忆化装饰器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache = LRUCache(maxsize=maxsize, ttl=ttl)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            key = _make_key(func.__name__, args, kwargs)
            result = cache.get(key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(key, result)
            return result

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            key = _make_key(func.__name__, args, kwargs)
            result = cache.get(key)
            if result is None:
                result = await func(*args, **kwargs)
                cache.set(key, result)
            return result

        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper.cache = cache
        return wrapper

    return decorator


def _make_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """生成缓存键"""
    key_parts = [func_name] + [str(a) for a in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
    key_str = ":".join(key_parts)
    return hashlib.md5(key_str.encode()).hexdigest()


class RateLimiter:
    """速率限制器"""

    def __init__(self, max_requests: int = 100, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: list[float] = []

    def allow(self) -> bool:
        """检查是否允许请求"""
        now = time.time()
        cutoff = now - self.window_seconds

        # Remove old requests
        self._requests = [t for t in self._requests if t > cutoff]

        if len(self._requests) < self.max_requests:
            self._requests.append(now)
            return True
        return False

    @property
    def remaining(self) -> int:
        """剩余请求数"""
        now = time.time()
        cutoff = now - self.window_seconds
        self._requests = [t for t in self._requests if t > cutoff]
        return max(0, self.max_requests - len(self._requests))

    @property
    def reset_time(self) -> float:
        """重置时间"""
        if not self._requests:
            return 0.0
        return self._requests[0] + self.window_seconds


class ConnectionPool:
    """连接池"""

    def __init__(self, max_size: int = 10, min_size: int = 2):
        self.max_size = max_size
        self.min_size = min_size
        self._pool: list[Any] = []
        self._in_use: set = set()
        self._factory: Callable | None = None

    def set_factory(self, factory: Callable) -> None:
        """设置连接工厂"""
        self._factory = factory

    async def acquire(self) -> Any:
        """获取连接"""
        if self._pool:
            conn = self._pool.pop()
            self._in_use.add(id(conn))
            return conn

        if len(self._in_use) < self.max_size and self._factory:
            conn = await self._factory()
            self._in_use.add(id(conn))
            return conn

        raise RuntimeError("Connection pool exhausted")

    async def release(self, conn: Any) -> None:
        """释放连接"""
        conn_id = id(conn)
        if conn_id in self._in_use:
            self._in_use.discard(conn_id)
            if len(self._pool) < self.max_size:
                self._pool.append(conn)

    @property
    def available(self) -> int:
        return len(self._pool)

    @property
    def in_use(self) -> int:
        return len(self._in_use)


class Timer:
    """计时器"""

    def __init__(self, name: str = ""):
        self.name = name
        self.start_time: float = 0
        self.end_time: float = 0
        self.elapsed_ms: float = 0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        self.end_time = time.time()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, *args):
        self.end_time = time.time()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000
