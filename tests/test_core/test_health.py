"""
健康检查测试
"""
import pytest
from behavior_core.health import (
    HealthChecker,
    HealthStatus,
    ComponentHealth,
)


class TestHealthChecker:
    @pytest.fixture
    def checker(self):
        return HealthChecker("test-service", "1.0.0")

    @pytest.mark.asyncio
    async def test_check_all_healthy(self, checker):
        checker.register_check("test", lambda: ComponentHealth(
            name="test", status=HealthStatus.HEALTHY
        ))

        report = await checker.check_all()
        assert report.status == HealthStatus.HEALTHY
        assert len(report.components) == 1

    @pytest.mark.asyncio
    async def test_check_unhealthy(self, checker):
        def failing_check():
            raise Exception("Connection failed")

        checker.register_check("failing", failing_check)

        report = await checker.check_all()
        assert report.status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_check_degraded(self, checker):
        checker.register_check("ok", lambda: ComponentHealth(
            name="ok", status=HealthStatus.HEALTHY
        ))
        checker.register_check("degraded", lambda: ComponentHealth(
            name="degraded", status=HealthStatus.DEGRADED
        ))

        report = await checker.check_all()
        assert report.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_uptime(self, checker):
        report = await checker.check_all()
        assert report.uptime_seconds >= 0
