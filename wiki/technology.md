# 技术选型

## 核心技术栈

| 组件 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| 语言 | Python | 3.11+ | 类型提示、性能优化 |
| Web 框架 | FastAPI | 0.109+ | 异步、高性能、自动文档 |
| 数据验证 | Pydantic | 2.5+ | 数据模型、序列化 |
| 消息队列 | Apache Pulsar | 2.11+ | 多租户、持久化 |
| 流处理 | Faust / PyFlink | 0.11 / 1.18 | 实时流计算 |
| 数据库 | PostgreSQL | 15+ | 关系型存储 |
| 缓存 | Redis | 7+ | 缓存、发布订阅 |
| 分析存储 | ClickHouse | 23+ | 列式存储、OLAP |
| 搜索 | Elasticsearch | 8+ | 全文搜索 |

## 技术选型理由

### 为什么选择 Python

1. **开发效率高**: 语法简洁，代码量少
2. **生态丰富**: 数据处理、AI/ML 库成熟
3. **异步支持**: asyncio 成熟，高并发能力强
4. **易于维护**: 代码可读性强，团队协作友好

### 为什么选择 FastAPI

1. **高性能**: 基于 Starlette 和 Pydantic，性能媲美 Node.js
2. **异步原生**: 完美支持 asyncio
3. **自动文档**: OpenAPI/Swagger 自动生成
4. **类型安全**: Pydantic 模型提供运行时验证

### 为什么选择 Faust

1. **纯 Python**: 无需 JVM，部署简单
2. **Kafka 原生**: 与 Kafka/Pulsar 无缝集成
3. **流处理**: 支持 Window、Join、Aggregation
4. **状态管理**: RocksDB 状态存储

### 为什么选择 PyFlink

1. **功能强大**: CEP、窗口、状态管理
2. **生态成熟**: 与 Java Flink 互通
3. **精确一次**: Checkpoint 机制保证
4. **大规模**: 支持大规模分布式部署

---

## 依赖配置

### pyproject.toml

```toml
[project]
name = "behavior-sense"
version = "1.0.0"
description = "User Behavior Stream Analytics Engine"
requires-python = ">=3.11"
readme = "README.md"

dependencies = [
    # Web 框架
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",

    # 消息队列
    "pulsar-client>=3.4.0",

    # 流处理 (选一)
    "faust-streaming>=0.11.0",
    # "apache-flink>=1.18.0",

    # 数据库
    "sqlalchemy>=2.0.0",
    "sqlmodel>=0.0.14",
    "asyncpg>=0.29.0",
    "aiomysql>=0.2.0",

    # 缓存
    "redis[asyncio]>=5.0.0",

    # ClickHouse
    "clickhouse-connect>=0.6.0",

    # Elasticsearch
    "elasticsearch[async]>=8.11.0",

    # HTTP 客户端
    "httpx>=0.26.0",

    # 数据处理
    "pandas>=2.1.0",
    "polars>=0.20.0",

    # 序列化
    "orjson>=3.9.0",

    # 日志
    "structlog>=24.1.0",

    # 配置
    "python-dotenv>=1.0.0",

    # 工具
    "tenacity>=8.2.0",
    "prometheus-client>=0.19.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
    "pre-commit>=3.6.0",
    "httpx>=0.26.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4"]

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## 项目结构

```
behavior-sense/
├── pyproject.toml           # 项目配置
├── README.md
├── .env.example             # 环境变量示例
├── docker-compose.yml       # 开发环境
│
├── behavior_core/           # 核心库
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── event.py         # 事件模型
│   │   └── user.py          # 用户模型
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py      # 配置管理
│   └── utils/
│       ├── __init__.py
│       ├── logging.py       # 日志工具
│       └── datetime.py      # 时间工具
│
├── behavior_mock/           # Mock 服务
│   ├── __init__.py
│   ├── main.py              # 入口
│   ├── generator.py         # 数据生成
│   ├── producer.py          # Pulsar 生产者
│   └── scenarios.py         # 场景配置
│
├── behavior_stream/         # 流处理
│   ├── __init__.py
│   ├── main.py
│   ├── app.py               # Faust 应用
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── aggregation.py   # 聚合任务
│   │   └── detection.py     # 检测任务
│   └── operators/
│       ├── __init__.py
│       └── window.py        # 窗口函数
│
├── behavior_rules/          # 规则引擎
│   ├── __init__.py
│   ├── main.py
│   ├── engine.py            # 规则引擎
│   ├── loader.py            # 规则加载
│   ├── models.py            # 规则模型
│   └── actions/
│       ├── __init__.py
│       ├── tagging.py       # 打标签
│       └── audit.py         # 触发审核
│
├── behavior_insight/        # 洞察服务
│   ├── __init__.py
│   ├── main.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── tags.py          # 标签 API
│   │   └── profile.py       # 画像 API
│   ├── services/
│   │   ├── __init__.py
│   │   └── tag_service.py
│   └── repositories/
│       ├── __init__.py
│       └── user_repo.py
│
├── behavior_audit/          # 审核服务
│   ├── __init__.py
│   ├── main.py
│   ├── routers/
│   └── services/
│
├── tests/
│   ├── conftest.py          # pytest 配置
│   ├── test_mock/
│   ├── test_stream/
│   ├── test_rules/
│   └── test_insight/
│
└── docker/
    ├── Dockerfile
    └── docker-compose.yml
```

---

## 开发环境

### 必需软件

| 软件 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 运行时 |
| Poetry / PDM | 最新 | 包管理 |
| Docker | 24+ | 容器运行时 |
| Docker Compose | 2.20+ | 本地环境 |

### 环境搭建

```bash
# 克隆项目
git clone https://github.com/behaviorsense/behavior-sense.git
cd behavior-sense

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -e ".[dev]"

# 复制配置文件
cp .env.example .env

# 启动基础设施
docker-compose up -d

# 运行测试
pytest
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  pulsar:
    image: apachepulsar/pulsar:2.11.2
    ports:
      - "6650:6650"
      - "8080:8080"
    environment:
      - PULSAR_PREFIX_clusterName=behavior-sense

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=behavior_sense

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  clickhouse:
    image: clickhouse/clickhouse-server:23-alpine
    ports:
      - "8123:8123"
      - "9000:9000"

  elasticsearch:
    image: elasticsearch:8.11.0
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
```

---

## 代码规范

### 命名约定

```python
# 模块名: 小写下划线
# behavior_mock/generator.py

# 类名: 大驼峰
class BehaviorGenerator:
    pass

# 函数/方法: 小写下划线
def generate_event() -> UserBehavior:
    pass

# 常量: 全大写下划线
MAX_RETRY_COUNT = 3

# 变量: 小写下划线
event_count = 100
```

### 类型注解

```python
from typing import AsyncIterator
from behavior_core.models.event import UserBehavior

async def stream_events(count: int) -> AsyncIterator[UserBehavior]:
    """流式生成事件"""
    for _ in range(count):
        yield generate_event()
```

### 日志规范

```python
import structlog

logger = structlog.get_logger()

async def process_event(event: UserBehavior):
    log = logger.bind(
        trace_id=event.event_id,
        user_id=event.user_id,
    )

    log.info("event_received", event_type=event.event_type)

    try:
        await handle_event(event)
        log.info("event_processed")
    except Exception as e:
        log.error("event_failed", error=str(e))
        raise
```

### 异常处理

```python
from fastapi import HTTPException

class BusinessException(Exception):
    """业务异常"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


# 全局异常处理
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=400,
        content={"code": exc.code, "message": exc.message},
    )
```

---

## 性能优化

### 异步数据库访问

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=10,
    max_overflow=20,
)

async with AsyncSession(engine) as session:
    result = await session.execute(select(User).where(User.id == user_id))
```

### Redis 连接池

```python
import redis.asyncio as redis

pool = redis.ConnectionPool(
    host="localhost",
    port=6379,
    max_connections=100,
)

client = redis.Redis(connection_pool=pool)
```

### 批量处理

```python
async def batch_process(events: list[UserBehavior], batch_size: int = 100):
    """批量处理事件"""
    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        await process_batch(batch)
```

---

## 监控集成

### Prometheus 指标

```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# 定义指标
EVENTS_TOTAL = Counter(
    'behavior_events_total',
    '处理的事件总数',
    ['event_type']
)

PROCESSING_TIME = Histogram(
    'behavior_processing_seconds',
    '事件处理时间'
)

# 使用指标
@PROCESSING_TIME.time()
async def process_event(event: UserBehavior):
    EVENTS_TOTAL.labels(event_type=event.event_type.value).inc()
    # 处理逻辑

# 暴露指标端点
@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

### 健康检查

```python
from fastapi import status
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    pulsar: str
    redis: str
    postgres: str

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        pulsar=await check_pulsar(),
        redis=await check_redis(),
        postgres=await check_postgres(),
    )
```

---

## 测试策略

### 单元测试

```python
# tests/test_mock/test_generator.py
import pytest
from behavior_mock.generator import BehaviorGenerator
from behavior_core.models.event import EventType

@pytest.fixture
def generator():
    return BehaviorGenerator(user_pool_size=100)

def test_generate_single_event(generator):
    event = generator.generate()
    assert event.user_id.startswith("user_")
    assert event.event_type in EventType

def test_generate_batch(generator):
    events = generator.generate_batch(10)
    assert len(events) == 10
```

### 异步测试

```python
# tests/test_insight/test_api.py
import pytest
from httpx import AsyncClient
from behavior_insight.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_get_user_tags(client):
    response = await client.get("/api/insight/user/user_001/tags")
    assert response.status_code == 200
```

### 集成测试

```python
# tests/conftest.py
import pytest
import docker
import time

@pytest.fixture(scope="session")
def docker_services():
    """启动 Docker 服务"""
    client = docker.from_env()
    compose = client.compose

    compose.up(detach=True)
    time.sleep(10)  # 等待服务启动

    yield

    compose.down()
```