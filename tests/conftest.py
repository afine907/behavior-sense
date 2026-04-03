"""
pytest 配置文件
"""
import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_user_id() -> str:
    """模拟用户ID"""
    return "user_001"


@pytest.fixture
def mock_event_data() -> dict:
    """模拟事件数据"""
    from datetime import datetime
    return {
        "user_id": "user_001",
        "event_type": "view",
        "timestamp": datetime.utcnow().isoformat(),
        "page_url": "/home",
        "properties": {"stay_duration": 30},
    }
