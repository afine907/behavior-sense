"""
API 测试配置和共享 fixtures
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

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
    """Insight 服务测试客户端"""
    async with _lifespan_manager(insight_app):
        async with AsyncClient(
            transport=ASGITransport(app=insight_app),
            base_url="http://test"
        ) as client:
            yield client


@pytest_asyncio.fixture
async def audit_client() -> AsyncGenerator[AsyncClient, None]:
    """Audit 服务测试客户端"""
    async with _lifespan_manager(audit_app):
        async with AsyncClient(
            transport=ASGITransport(app=audit_app),
            base_url="http://test"
        ) as client:
            yield client


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
