"""
API 测试配置和共享 fixtures
"""
import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# 检测测试模式
TEST_REAL_DEPS = os.getenv("TEST_REAL_DEPS", "").lower() in ("1", "true", "yes")

# 导入各服务的 FastAPI 应用
from behavior_audit.main import app as audit_app
from behavior_insight.main import app as insight_app
from behavior_mock.main import app as mock_app
from behavior_rules.main import app as rules_app


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@asynccontextmanager
async def _lifespan_manager(app):
    """管理应用生命周期的上下文管理器"""
    lifespan_context = getattr(app.router, "lifespan_context", None)
    if lifespan_context:
        async with lifespan_context(app):
            yield
    else:
        yield


# ============== Mock Redis 实现 ==============

class MockRedis:
    """完整的 Mock Redis 客户端"""

    def __init__(self):
        self.data: dict[str, dict] = {}
        self.sets: dict[str, set] = {}
        self.strings: dict[str, str] = {}
        self.expirations: dict[str, float] = {}
        self.published: list[tuple[str, str]] = []

    async def hgetall(self, key: str) -> dict:
        return self.data.get(key, {})

    async def hget(self, key: str, field: str) -> str | None:
        return self.data.get(key, {}).get(field)

    async def hset(self, key: str, field: str = None, value: str = None, mapping: dict = None) -> int:
        if key not in self.data:
            self.data[key] = {}
        if mapping:
            self.data[key].update(mapping)
        elif field and value is not None:
            self.data[key][field] = value
        return 1

    async def hdel(self, key: str, *fields) -> int:
        if key in self.data:
            deleted = 0
            for field in fields:
                if field in self.data[key]:
                    del self.data[key][field]
                    deleted += 1
            return deleted
        return 0

    async def get(self, key: str) -> str | None:
        return self.strings.get(key)

    async def set(self, key: str, value: str, ex: int = None) -> bool:
        self.strings[key] = value
        return True

    async def delete(self, key: str) -> int:
        count = 0
        if key in self.data:
            del self.data[key]
            count += 1
        if key in self.sets:
            del self.sets[key]
            count += 1
        if key in self.strings:
            del self.strings[key]
            count += 1
        return count

    async def sadd(self, key: str, *members) -> int:
        if key not in self.sets:
            self.sets[key] = set()
        added = 0
        for member in members:
            if member not in self.sets[key]:
                self.sets[key].add(member)
                added += 1
        return added

    async def srem(self, key: str, *members) -> int:
        if key not in self.sets:
            return 0
        removed = 0
        for member in members:
            if member in self.sets[key]:
                self.sets[key].remove(member)
                removed += 1
        return removed

    async def smembers(self, key: str) -> set:
        return self.sets.get(key, set())

    async def exists(self, key: str) -> bool:
        return key in self.data or key in self.sets or key in self.strings

    async def expire(self, key: str, seconds: int) -> bool:
        if await self.exists(key):
            self.expirations[key] = asyncio.get_event_loop().time() + seconds
            return True
        return False

    async def ttl(self, key: str) -> int:
        if key not in self.expirations:
            return -1
        remaining = self.expirations[key] - asyncio.get_event_loop().time()
        return max(0, int(remaining))

    async def publish(self, channel: str, message: str) -> int:
        self.published.append((channel, message))
        return 1

    async def ping(self) -> bool:
        return True

    async def close(self):
        pass

    async def aclose(self):
        pass


# ============== Mock 服务 Fixtures ==============

@pytest_asyncio.fixture
async def mock_client() -> AsyncGenerator[AsyncClient, None]:
    """Mock 服务测试客户端"""
    async with AsyncClient(
        transport=ASGITransport(app=mock_app),
        base_url="http://test"
    ) as client:
        yield client


# ============== Rules 服务 Fixtures ==============

@pytest_asyncio.fixture
async def rules_client() -> AsyncGenerator[AsyncClient, None]:
    """Rules 服务测试客户端"""
    async with AsyncClient(
        transport=ASGITransport(app=rules_app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def sample_rule_create() -> dict:
    """示例规则创建数据"""
    return {
        "name": "高价值用户识别",
        "description": "识别购买次数超过5次的用户",
        "condition": "purchase_count >= 5",
        "priority": 1,
        "enabled": True,
        "actions": [
            {
                "type": "TAG_USER",
                "params": {"tags": ["high_value"]}
            }
        ],
        "tags": ["marketing", "segmentation"]
    }


@pytest.fixture
def sample_context() -> dict:
    """示例评估上下文"""
    return {
        "user_id": "user_001",
        "purchase_count": 10,
        "total_amount": 5000.0,
        "view_count": 50,
        "click_count": 20
    }


# ============== Insight 服务 Fixtures ==============

@pytest_asyncio.fixture
async def insight_client() -> AsyncGenerator[AsyncClient, None]:
    """Insight 服务测试客户端

    模式选择：
    - TEST_REAL_DEPS=1: 使用真实 PostgreSQL + Redis
    - 默认: 使用 Mock 依赖
    """
    if TEST_REAL_DEPS:
        # 真实依赖模式
        async with _lifespan_manager(insight_app):
            async with AsyncClient(
                transport=ASGITransport(app=insight_app),
                base_url="http://test"
            ) as client:
                yield client
    else:
        # Mock 模式：注入 Mock 依赖
        mock_redis_instance = MockRedis()

        # 替换应用状态中的 Redis
        original_redis = getattr(insight_app.state, "redis", None)
        insight_app.state.redis = mock_redis_instance

        async with AsyncClient(
            transport=ASGITransport(app=insight_app),
            base_url="http://test"
        ) as client:
            yield client

        # 恢复原始状态
        if original_redis:
            insight_app.state.redis = original_redis


@pytest_asyncio.fixture
async def audit_client() -> AsyncGenerator[AsyncClient, None]:
    """Audit 服务测试客户端

    模式选择：
    - TEST_REAL_DEPS=1: 使用真实 PostgreSQL + Redis
    - 默认: 使用 Mock 依赖
    """
    if TEST_REAL_DEPS:
        # 真实依赖模式
        async with _lifespan_manager(audit_app):
            async with AsyncClient(
                transport=ASGITransport(app=audit_app),
                base_url="http://test"
            ) as client:
                yield client
    else:
        # Mock 模式：注入 Mock 依赖
        mock_redis_instance = MockRedis()

        # 替换应用状态中的 Redis
        original_redis = getattr(audit_app.state, "redis", None)
        audit_app.state.redis = mock_redis_instance

        async with AsyncClient(
            transport=ASGITransport(app=audit_app),
            base_url="http://test"
        ) as client:
            yield client

        # 恢复原始状态
        if original_redis:
            audit_app.state.redis = original_redis


@pytest.fixture
def sample_tag_update() -> dict:
    """示例标签更新数据"""
    return {
        "tag_name": "level",
        "tag_value": "vip",
        "source": "MANUAL",
        "confidence": 1.0
    }


@pytest.fixture
def sample_profile_update() -> dict:
    """示例画像更新数据"""
    return {
        "basic_info": {
            "name": "Test User",
            "email": "test@example.com"
        },
        "behavior_tags": ["active", "high_value"],
        "risk_level": "low"
    }


# ============== Audit 服务数据 Fixtures ==============

@pytest.fixture
def sample_order_create() -> dict:
    """示例工单创建数据"""
    return {
        "user_id": "user_001",
        "rule_id": "rule_001",
        "trigger_data": {
            "event_type": "suspicious_login",
            "ip_address": "192.168.1.100",
            "location": "Beijing"
        },
        "audit_level": "medium"
    }


@pytest.fixture
def sample_assign_request() -> dict:
    """示例分配请求"""
    return {
        "assignee": "reviewer_001"
    }


@pytest.fixture
def sample_review_request() -> dict:
    """示例审核请求"""
    return {
        "status": "approved",
        "note": "审核通过，用户行为正常",
        "reviewer": "reviewer_001"
    }


# ============== 测试数据生成 ==============

@pytest.fixture
def generate_user_id() -> str:
    """生成唯一用户ID"""
    import uuid
    return f"user_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def generate_rule_id() -> str:
    """生成唯一规则ID"""
    import uuid
    return f"rule_{uuid.uuid4().hex[:8]}"
