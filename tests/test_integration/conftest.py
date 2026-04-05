"""
集成测试配置和共享 fixtures

提供两种测试模式：
1. Mock 模式：使用内存数据库和 Mock Redis，无需外部依赖
2. 真实依赖模式：连接真实 PostgreSQL 和 Redis，用于 CI 验证

使用方式：
- 默认运行 Mock 模式（快速）
- 设置环境变量 TEST_REAL_DEPS=1 运行真实依赖模式
"""
import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch
import uuid

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


# ============== 工具函数 ==============

@asynccontextmanager
async def _lifespan_manager(app):
    """管理应用生命周期的上下文管理器"""
    lifespan_context = getattr(app.router, "lifespan_context", None)
    if lifespan_context:
        async with lifespan_context(app):
            yield
    else:
        yield


# ============== ID 生成 Fixtures ==============

@pytest.fixture
def generate_user_id() -> str:
    """生成唯一用户ID"""
    return f"user_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def generate_rule_id() -> str:
    """生成唯一规则ID"""
    return f"rule_{uuid.uuid4().hex[:8]}"


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


# ============== 内存数据库实现 ==============

class InMemoryDatabase:
    """内存数据库模拟（用于无依赖测试）"""

    def __init__(self):
        self.users: dict[str, dict] = {}
        self.user_stats: dict[str, dict] = {}
        self.audit_orders: dict[str, dict] = {}
        self._next_id = 1

    def _generate_id(self) -> str:
        self._next_id += 1
        return f"id_{self._next_id:08d}"


# ============== 无依赖服务 Fixtures ==============

@pytest_asyncio.fixture
async def mock_redis() -> MockRedis:
    """提供 Mock Redis 实例"""
    return MockRedis()


@pytest_asyncio.fixture
async def in_memory_db() -> InMemoryDatabase:
    """提供内存数据库实例"""
    return InMemoryDatabase()


@pytest_asyncio.fixture
async def mock_client() -> AsyncGenerator[AsyncClient, None]:
    """Mock 服务测试客户端（无外部依赖）"""
    async with AsyncClient(
        transport=ASGITransport(app=mock_app),
        base_url="http://test-mock"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def rules_client() -> AsyncGenerator[AsyncClient, None]:
    """Rules 服务测试客户端（无外部依赖）"""
    async with AsyncClient(
        transport=ASGITransport(app=rules_app),
        base_url="http://test-rules"
    ) as client:
        yield client


# ============== 真实依赖服务 Fixtures ==============

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
                base_url="http://test-insight"
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
            base_url="http://test-insight"
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
                base_url="http://test-audit"
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
            base_url="http://test-audit"
        ) as client:
            yield client

        # 恢复原始状态
        if original_redis:
            audit_app.state.redis = original_redis


# ============== 多服务集成上下文 ==============

class MultiServiceContext:
    """多服务集成上下文"""

    def __init__(
        self,
        rules_client: AsyncClient,
        insight_client: AsyncClient,
        audit_client: AsyncClient
    ):
        self.rules = rules_client
        self.insight = insight_client
        self.audit = audit_client


@pytest_asyncio.fixture
async def multi_service_context(
    rules_client: AsyncClient,
    insight_client: AsyncClient,
    audit_client: AsyncClient
) -> MultiServiceContext:
    """多服务集成上下文"""
    return MultiServiceContext(
        rules_client=rules_client,
        insight_client=insight_client,
        audit_client=audit_client
    )


# ============== 服务间通信 Mock ==============

@pytest.fixture
def mock_rules_to_insight_client():
    """Mock Rules 服务到 Insight 服务的 HTTP 客户端"""
    mock_client = AsyncMock(spec=AsyncClient)

    with patch("behavior_rules.actions.tagging.get_shared_client") as mock_get:
        mock_get.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_rules_to_audit_client():
    """Mock Rules 服务到 Audit 服务的 HTTP 客户端"""
    mock_client = AsyncMock(spec=AsyncClient)

    with patch("behavior_rules.actions.audit.get_audit_client") as mock_get:
        mock_get.return_value = mock_client
        yield mock_client


# ============== 测试数据 Fixtures ==============

@pytest.fixture
def sample_high_value_rule() -> dict:
    """高价值用户规则"""
    return {
        "name": "高价值用户识别",
        "description": "购买次数>=5且总金额>1000的用户",
        "condition": "purchase_count >= 5 and total_amount > 1000",
        "priority": 1,
        "enabled": True,
        "actions": [
            {
                "type": "TAG_USER",
                "params": {"tags": ["high_value"]}
            }
        ],
        "tags": ["marketing"]
    }


@pytest.fixture
def sample_suspicious_rule() -> dict:
    """可疑行为规则"""
    return {
        "name": "可疑登录检测",
        "description": "登录失败次数>=5的用户",
        "condition": "login_fail_count >= 5",
        "priority": 10,
        "enabled": True,
        "actions": [
            {
                "type": "TRIGGER_AUDIT",
                "params": {"level": "HIGH", "reason": "检测到可疑登录行为"}
            }
        ],
        "tags": ["security"]
    }


@pytest.fixture
def sample_user_context_high_value() -> dict:
    """高价值用户评估上下文"""
    return {
        "user_id": "user_high_value_001",
        "purchase_count": 10,
        "total_amount": 5000.0,
        "view_count": 100,
        "click_count": 50
    }


@pytest.fixture
def sample_user_context_suspicious() -> dict:
    """可疑用户评估上下文"""
    return {
        "user_id": "user_suspicious_001",
        "login_fail_count": 7,
        "last_login_ip": "192.168.1.100"
    }


# ============== 辅助函数 ==============

async def wait_for_condition(
    condition_func,
    timeout: float = 5.0,
    interval: float = 0.1
) -> bool:
    """等待条件满足"""
    elapsed = 0.0
    while elapsed < timeout:
        if await condition_func():
            return True
        await asyncio.sleep(interval)
        elapsed += interval
    return False


def assert_tag_created(response_data: dict, tag_name: str, source: str = "rule"):
    """断言标签已创建"""
    assert "tags" in response_data or "tag_name" in response_data
    if "tags" in response_data:
        tags = response_data.get("tags", {})
        assert tag_name in tags, f"Tag {tag_name} not found in response"


def assert_audit_order_created(response_data: dict, user_id: str):
    """断言审核工单已创建"""
    assert response_data.get("user_id") == user_id
    assert "id" in response_data or "order_id" in response_data
    assert response_data.get("status") in ["pending", "PENDING"]


# ============== pytest 配置 ==============

def pytest_configure(config):
    """pytest 配置钩子"""
    config.addinivalue_line(
        "markers", "real_deps: 需要真实外部依赖的测试"
    )
    config.addinivalue_line(
        "markers", "mock_deps: 使用 Mock 依赖的测试"
    )


def pytest_collection_modifyitems(config, items):
    """根据测试模式过滤测试用例"""
    if not TEST_REAL_DEPS:
        # Mock 模式下跳过需要真实依赖的测试
        skip_real_deps = pytest.mark.skip(
            reason="需要设置 TEST_REAL_DEPS=1 运行真实依赖测试"
        )
        for item in items:
            if "real_deps" in item.keywords:
                item.add_marker(skip_real_deps)
