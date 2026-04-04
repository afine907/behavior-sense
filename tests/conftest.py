"""
pytest 配置文件 - Monorepo 结构支持
"""
import sys
import pytest
import asyncio
from pathlib import Path
from typing import Generator

# 添加 monorepo 源码路径到 sys.path
ROOT_DIR = Path(__file__).parent.parent
LIBS_CORE = ROOT_DIR / "libs" / "core" / "src"
PACKAGES_DIR = ROOT_DIR / "packages"

# 添加核心库
if str(LIBS_CORE) not in sys.path:
    sys.path.insert(0, str(LIBS_CORE))

# 添加所有服务包
for service in PACKAGES_DIR.iterdir():
    if service.is_dir():
        src_dir = service / "src"
        if src_dir.exists() and str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))


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
