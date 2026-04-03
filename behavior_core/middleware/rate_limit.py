"""
API 限流中间件

基于 Redis 的滑动窗口限流算法。
"""
import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

from behavior_core.config.settings import get_settings
from behavior_core.utils.logging import get_logger


logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    限流中间件

    使用滑动窗口算法限制 API 请求频率。
    """

    def __init__(
        self,
        app,
        redis_client: redis.Redis | None = None,
        requests_per_minute: int = 100,
        window_seconds: int = 60,
        key_prefix: str = "rate_limit:",
    ):
        """
        初始化限流中间件

        Args:
            app: FastAPI 应用
            redis_client: Redis 客户端
            requests_per_minute: 每分钟最大请求数
            window_seconds: 时间窗口（秒）
            key_prefix: Redis 键前缀
        """
        super().__init__(app)
        self.redis_client = redis_client
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端 IP"""
        # 检查代理头
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 直接连接的客户端
        if request.client:
            return request.client.host

        return "unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        处理请求

        Args:
            request: 请求对象
            call_next: 下一个处理器

        Returns:
            响应对象
        """
        # 健康检查和 metrics 端点不限流
        if request.url.path in ["/health", "/ready", "/metrics", "/openapi.json", "/docs", "/redoc"]:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        key = f"{self.key_prefix}{client_ip}"

        # 如果没有 Redis 客户端，跳过限流（使用内存限流）
        if self.redis_client is None:
            return await self._memory_rate_limit(request, call_next, key)

        try:
            return await self._redis_rate_limit(request, call_next, key)
        except redis.RedisError as e:
            logger.warning("Rate limit redis error, allowing request", error=str(e))
            return await call_next(request)

    async def _redis_rate_limit(
        self, request: Request, call_next, key: str
    ) -> Response:
        """使用 Redis 进行限流"""
        current_time = time.time()
        window_start = current_time - self.window_seconds

        pipe = self.redis_client.pipeline()
        # 移除窗口外的记录
        pipe.zremrangebyscore(key, 0, window_start)
        # 获取当前窗口内的请求数
        pipe.zcard(key)
        # 添加当前请求
        pipe.zadd(key, {str(current_time): current_time})
        # 设置过期时间
        pipe.expire(key, self.window_seconds)

        results = await pipe.execute()
        request_count = results[1]

        if request_count >= self.requests_per_minute:
            logger.warning(
                "Rate limit exceeded",
                client_ip=self._get_client_ip(request),
                request_count=request_count,
                limit=self.requests_per_minute,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "code": 3001,
                    "message": "Rate limit exceeded. Please try again later.",
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        return await call_next(request)

    async def _memory_rate_limit(
        self, request: Request, call_next, key: str
    ) -> Response:
        """使用内存进行限流（备用方案）"""
        current_time = time.time()
        window_start = current_time - self.window_seconds

        # 使用类级别的字典存储限流数据
        if not hasattr(self, "_rate_limit_store"):
            self._rate_limit_store: dict[str, list[float]] = {}

        if key not in self._rate_limit_store:
            self._rate_limit_store[key] = []

        # 清理过期记录
        self._rate_limit_store[key] = [
            t for t in self._rate_limit_store[key] if t > window_start
        ]

        request_count = len(self._rate_limit_store[key])

        if request_count >= self.requests_per_minute:
            logger.warning(
                "Rate limit exceeded (memory)",
                client_ip=self._get_client_ip(request),
                request_count=request_count,
                limit=self.requests_per_minute,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "code": 3001,
                    "message": "Rate limit exceeded. Please try again later.",
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        # 记录当前请求
        self._rate_limit_store[key].append(current_time)

        return await call_next(request)


# 限流异常
class RateLimitExceeded(Exception):
    """限流异常"""
    pass
