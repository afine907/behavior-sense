"""
健康检查系统
"""
import asyncio
import time
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable

import httpx
from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class HealthStatus(str, Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentHealth(BaseModel):
    """组件健康状态"""
    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)
    last_checked: datetime = Field(default_factory=_utc_now)


class HealthReport(BaseModel):
    """健康报告"""
    status: HealthStatus
    version: str
    uptime_seconds: float
    components: list[ComponentHealth] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=_utc_now)

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY


class HealthChecker:
    """健康检查器"""

    def __init__(self, service_name: str, version: str = "2.0.0"):
        self.service_name = service_name
        self.version = version
        self.start_time = time.time()
        self._checks: dict[str, Callable] = {}
        self._last_results: dict[str, ComponentHealth] = {}

    def register_check(self, name: str, check_func: Callable) -> None:
        """注册健康检查"""
        self._checks[name] = check_func

    async def check_component(self, name: str) -> ComponentHealth:
        """检查单个组件"""
        check_func = self._checks.get(name)
        if not check_func:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                message="No check registered",
            )

        start = time.time()
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()

            latency = (time.time() - start) * 1000

            if isinstance(result, ComponentHealth):
                result.latency_ms = latency
                return result

            return ComponentHealth(
                name=name,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=latency,
            )

    async def check_all(self) -> HealthReport:
        """检查所有组件"""
        components = []
        overall_status = HealthStatus.HEALTHY

        for name in self._checks:
            component = await self.check_component(name)
            components.append(component)
            self._last_results[name] = component

            # Update overall status
            if component.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif component.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED

        return HealthReport(
            status=overall_status,
            version=self.version,
            uptime_seconds=time.time() - self.start_time,
            components=components,
        )

    def get_last_results(self) -> dict[str, ComponentHealth]:
        """获取上次检查结果"""
        return dict(self._last_results)


# Pre-built health checks

async def check_http_endpoint(url: str, timeout: float = 5.0) -> ComponentHealth:
    """检查HTTP端点"""
    try:
        async with httpx.AsyncClient() as client:
            start = time.time()
            response = await client.get(url, timeout=timeout)
            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                return ComponentHealth(
                    name=url,
                    status=HealthStatus.HEALTHY,
                    latency_ms=latency,
                    details={"status_code": response.status_code},
                )
            else:
                return ComponentHealth(
                    name=url,
                    status=HealthStatus.DEGRADED,
                    message=f"HTTP {response.status_code}",
                    latency_ms=latency,
                )
    except Exception as e:
        return ComponentHealth(
            name=url,
            status=HealthStatus.UNHEALTHY,
            message=str(e),
        )


def check_redis_available() -> ComponentHealth:
    """检查Redis可用性"""
    try:
        import redis
        r = redis.Redis()
        r.ping()
        return ComponentHealth(
            name="redis",
            status=HealthStatus.HEALTHY,
        )
    except Exception as e:
        return ComponentHealth(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            message=str(e),
        )


async def check_clickhouse_available(url: str = "http://localhost:8123") -> ComponentHealth:
    """检查ClickHouse可用性"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/ping", timeout=5.0)
            if response.status_code == 200:
                return ComponentHealth(
                    name="clickhouse",
                    status=HealthStatus.HEALTHY,
                )
            else:
                return ComponentHealth(
                    name="clickhouse",
                    status=HealthStatus.UNHEALTHY,
                    message=f"HTTP {response.status_code}",
                )
    except Exception as e:
        return ComponentHealth(
            name="clickhouse",
            status=HealthStatus.UNHEALTHY,
            message=str(e),
        )


def check_memory_usage(threshold_pct: float = 90.0) -> ComponentHealth:
    """检查内存使用"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        if memory.percent > threshold_pct:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.DEGRADED,
                message=f"Memory usage {memory.percent}% exceeds threshold {threshold_pct}%",
                details={"percent": memory.percent, "available_gb": memory.available / (1024**3)},
            )
        return ComponentHealth(
            name="memory",
            status=HealthStatus.HEALTHY,
            details={"percent": memory.percent, "available_gb": memory.available / (1024**3)},
        )
    except ImportError:
        return ComponentHealth(
            name="memory",
            status=HealthStatus.UNKNOWN,
            message="psutil not installed",
        )


def check_disk_usage(path: str = "/", threshold_pct: float = 90.0) -> ComponentHealth:
    """检查磁盘使用"""
    try:
        import psutil
        disk = psutil.disk_usage(path)
        if disk.percent > threshold_pct:
            return ComponentHealth(
                name="disk",
                status=HealthStatus.DEGRADED,
                message=f"Disk usage {disk.percent}% exceeds threshold {threshold_pct}%",
                details={"percent": disk.percent, "free_gb": disk.free / (1024**3)},
            )
        return ComponentHealth(
            name="disk",
            status=HealthStatus.HEALTHY,
            details={"percent": disk.percent, "free_gb": disk.free / (1024**3)},
        )
    except ImportError:
        return ComponentHealth(
            name="disk",
            status=HealthStatus.UNKNOWN,
            message="psutil not installed",
        )
