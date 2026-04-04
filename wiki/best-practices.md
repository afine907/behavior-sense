# Python Backend Best Practices

> This document covers best practices for the BehaviorSense project using FastAPI, Pydantic, SQLAlchemy, Faust, and related technologies.

---

## Project Structure (Monorepo)

```
behavior-sense/
├── libs/core/                   # Shared library
│   └── src/behavior_core/
│       ├── config/              # Settings
│       ├── models/              # Pydantic models
│       ├── security/            # Auth, JWT
│       ├── middleware/          # Rate limit, tracing
│       └── utils/               # Logging, datetime
│
├── packages/                    # Microservices
│   ├── audit/src/behavior_audit/
│   ├── insight/src/behavior_insight/
│   ├── mock/src/behavior_mock/
│   ├── rules/src/behavior_rules/
│   └── stream/src/behavior_stream/
│
└── tests/                       # Test suites
```

---

## Package Management with uv

### Installation

```bash
# Install all dependencies
uv sync

# Add dependency
uv add httpx

# Add to specific package
uv add --package behavior-audit httpx

# Add dev dependency
uv add --group dev black

# Run commands
uv run pytest
uv run ruff check libs/ packages/
```

### Workspace Configuration

```toml
# pyproject.toml
[tool.uv.workspace]
members = [
    "libs/core",
    "packages/audit",
    "packages/insight",
    "packages/mock",
    "packages/rules",
    "packages/stream",
]

[tool.uv.sources]
behavior-core = { workspace = true }
```

---

## FastAPI 最佳实践

### 1. 依赖注入模式

```python
# ✅ 推荐：使用依赖注入
from fastapi import Depends
from typing import Annotated

async def get_db():
    async with AsyncSession(engine) as session:
        yield session

DbSession = Annotated[AsyncSession, Depends(get_db)]

@app.get("/users/{user_id}")
async def get_user(user_id: str, db: DbSession):
    ...

# ❌ 避免：直接在路由中创建连接
@app.get("/users/{user_id}")
async def get_user(user_id: str):
    async with AsyncSession(engine) as db:  # 每次都创建新连接
        ...
```

### 2. 异常处理

```python
# ✅ 推荐：全局异常处理器
from fastapi import Request
from fastapi.responses import JSONResponse

class BusinessException(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=400,
        content={"code": exc.code, "message": exc.message},
    )

# ❌ 避免：在每个路由中 try-catch
@app.get("/users/{user_id}")
async def get_user(user_id: str):
    try:
        ...
    except BusinessException as e:
        return JSONResponse(status_code=400, content={...})
```

### 3. 响应模型

```python
# ✅ 推荐：明确定义响应模型
from pydantic import BaseModel

class UserResponse(BaseModel):
    user_id: str
    name: str
    tags: list[str]

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str) -> UserResponse:
    ...

# ❌ 避免：返回 dict
@app.get("/users/{user_id}")
async def get_user(user_id: str):
    return {"user_id": user_id, ...}  # 没有类型检查
```

### 4. 后台任务

```python
# ✅ 推荐：使用 BackgroundTasks
from fastapi import BackgroundTasks

async def send_notification(user_id: str):
    ...

@app.post("/users")
async def create_user(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_notification, user_id)
    return {"status": "ok"}
```

---

## Pydantic 最佳实践

### 1. 模型复用

```python
# ✅ 推荐：使用模型组合
class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    created_at: datetime

# ❌ 避免：重复定义字段
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    name: str  # 重复
    email: str  # 重复
    created_at: datetime
```

### 2. 验证器

```python
# ✅ 推荐：使用 field_validator
from pydantic import field_validator

class User(BaseModel):
    email: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError('Invalid email')
        return v.lower()
```

### 3. 配置类

```python
# ✅ 推荐：使用 ConfigDict
from pydantic import ConfigDict

class User(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_min_length=1,
        validate_assignment=True,
    )
```

---

## SQLAlchemy 异步最佳实践

### 1. 连接管理

```python
# ✅ 推荐：使用 sessionmaker
from sqlalchemy.ext.asyncio import async_sessionmaker

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 重要！
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 2. 查询优化

```python
# ✅ 推荐：使用 selectinload 预加载
from sqlalchemy.orm import selectinload

stmt = select(User).options(
    selectinload(User.orders),
    selectinload(User.tags),
)

# ❌ 避免：N+1 查询问题
users = await db.execute(select(User))
for user in users:
    orders = await db.execute(select(Order).where(Order.user_id == user.id))  # N+1!
```

### 3. 批量操作

```python
# ✅ 推荐：批量插入
async with AsyncSessionLocal() as db:
    db.add_all([User(name=f"user_{i}") for i in range(1000)])
    await db.commit()

# ❌ 避免：逐条插入
async with AsyncSessionLocal() as db:
    for i in range(1000):
        db.add(User(name=f"user_{i}"))
        await db.commit()  # 1000 次提交！
```

---

## Redis 异步最佳实践

### 1. 连接池

```python
# ✅ 推荐：使用连接池
import redis.asyncio as redis

pool = redis.ConnectionPool(
    host="localhost",
    port=6379,
    max_connections=100,
    decode_responses=True,
)

client = redis.Redis(connection_pool=pool)

# 应用关闭时
await client.close()
await pool.disconnect()
```

### 2. Pipeline 批量操作

```python
# ✅ 推荐：使用 Pipeline
async with client.pipeline() as pipe:
    pipe.set("key1", "value1")
    pipe.set("key2", "value2")
    pipe.set("key3", "value3")
    await pipe.execute()  # 一次网络往返

# ❌ 避免：逐条操作
await client.set("key1", "value1")
await client.set("key2", "value2")
await client.set("key3", "value3")  # 3 次网络往返
```

---

## 错误处理模式

### 1. 服务层异常

```python
# behavior_core/exceptions.py
class BehaviorSenseException(Exception):
    """基础异常"""
    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}

class NotFoundException(BehaviorSenseException):
    """资源不存在"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} not found: {identifier}",
        )

class ValidationException(BehaviorSenseException):
    """验证失败"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            details=details,
        )
```

### 2. 全局异常处理

```python
# behavior_core/exception_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse

async def behavior_exception_handler(request: Request, exc: BehaviorSenseException):
    return JSONResponse(
        status_code=400,
        content={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )

async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"code": "INTERNAL_ERROR", "message": "Internal server error"},
    )
```

---

## 性能优化建议

### 1. 使用 orjson 替代 json

```python
# ✅ 推荐
import orjson

data = orjson.dumps(event.model_dump())  # 快 3-5 倍

# ❌ 避免
import json
data = json.dumps(event.model_dump())
```

### 2. 异步并发

```python
# ✅ 推荐：并发执行
import asyncio

results = await asyncio.gather(
    get_user(user_id),
    get_user_tags(user_id),
    get_user_orders(user_id),
)

# ❌ 避免：串行执行
user = await get_user(user_id)
tags = await get_user_tags(user_id)
orders = await get_user_orders(user_id)
```

### 3. 缓存策略

```python
# ✅ 推荐：多级缓存
async def get_user_with_cache(user_id: str) -> User:
    # L1: 本地缓存
    if user_id in local_cache:
        return local_cache[user_id]

    # L2: Redis
    cached = await redis.get(f"user:{user_id}")
    if cached:
        return User.model_validate_json(cached)

    # L3: 数据库
    user = await db.get(User, user_id)
    if user:
        await redis.setex(f"user:{user_id}", 3600, user.model_dump_json())
        local_cache[user_id] = user

    return user
```

---

## Faust 流处理最佳实践

### 1. 应用配置

```python
# ✅ 推荐：完整配置
import faust

app = faust.App(
    'behavior-sense',
    broker='pulsar://localhost:6650',
    store='rocksdb://',  # 持久化状态存储
    topic_replication_factor=3,
    topic_partitions=4,
    table_standby_replicas=2,
    worker_timeout=3600,  # 1小时超时
)

# ❌ 避免：使用内存存储
app = faust.App(
    'behavior-sense',
    broker='pulsar://localhost:6650',
    store='memory://',  # 重启丢失状态！
)
```

### 2. Topic 定义

```python
# ✅ 推荐：明确 Topic 配置
behavior_topic = app.topic(
    'user-behavior',
    key_type=str,
    value_type=UserBehavior,
    partitions=4,
    retention=timedelta(days=7),
)

# ❌ 避免：默认配置
behavior_topic = app.topic('user-behavior')  # 使用默认配置
```

### 3. 状态管理

```python
# ✅ 推荐：使用 Table 管理状态
user_stats = app.Table(
    'user_stats',
    default=dict,
    partitions=4,
    key_type=str,
    value_type=dict,
)

# 窗口表
user_window_stats = app.Table(
    'user_window_stats',
    default=int,
).hopping(
    size=timedelta(minutes=1),
    step=timedelta(minutes=1),
    expires=timedelta(hours=1),
)
```

### 4. Agent 处理

```python
# ✅ 推荐：正确处理异常
@app.agent(behavior_topic)
async def process_events(events):
    async for event in events:
        try:
            await process_event(event)
        except Exception as e:
            logger.error(f"处理失败: {e}", event_id=event.event_id)
            # 发送到死信队列
            await dead_letter_topic.send(value=event)
            continue

# ❌ 避免：静默失败
@app.agent(behavior_topic)
async def process_events(events):
    async for event in events:
        try:
            await process_event(event)
        except:
            pass  # 吞掉异常！
```

---

## Pulsar 消息队列最佳实践

### 1. 生产者配置

```python
# ✅ 推荐：批量发送
producer = client.create_producer(
    topic,
    batching_enabled=True,
    batching_max_messages=1000,
    batching_max_publish_delay_ms=10,
    max_pending_messages=10000,
    block_if_queue_full=True,
)

# ❌ 避免：同步逐条发送
for event in events:
    producer.send(event)  # 每条都等待确认
```

### 2. 消费者配置

```python
# ✅ 推荐：配置重试和死信
consumer = client.subscribe(
    topic,
    subscription_name='processor',
    consumer_type=ConsumerType.Shared,
    dead_letter_policy=DeadLetterPolicy(
        max_redeliver_count=3,
        dead_letter_topic='dead-letter',
    ),
    negative_ack_redelivery_delay_ms=60000,  # 1分钟后重试
)
```

### 3. 消息确认

```python
# ✅ 推荐：处理成功后再确认
async for msg in consumer:
    try:
        await process_message(msg)
        consumer.acknowledge(msg)
    except Exception as e:
        consumer.negative_acknowledge(msg)  # 重试

# ❌ 避免：先确认再处理
async for msg in consumer:
    consumer.acknowledge(msg)  # 先确认
    await process_message(msg)  # 失败了消息已丢失！
```

---

## structlog 日志最佳实践

### 1. 配置

```python
# ✅ 推荐：结构化日志
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()
logger.info("event_processed", event_id="123", user_id="user_001")
```

### 2. 上下文绑定

```python
# ✅ 推荐：绑定上下文
log = logger.bind(
    trace_id=event.event_id,
    user_id=event.user_id,
)

log.info("processing_started")
try:
    await process(event)
    log.info("processing_completed")
except Exception as e:
    log.error("processing_failed", error=str(e))
```

---

## pytest 测试最佳实践

### 1. 异步测试

```python
# ✅ 推荐：使用 pytest-asyncio
import pytest

@pytest.mark.asyncio
async def test_create_user():
    async with AsyncSession(engine) as db:
        user = await UserService(db).create(name="test")
        assert user.id is not None
```

### 2. Fixture 复用

```python
# ✅ 推荐：conftest.py 共享 fixture
import pytest

@pytest.fixture
async def db_session():
    async with AsyncSession(engine) as session:
        yield session

@pytest.fixture
def mock_redis():
    class MockRedis:
        data = {}
        async def get(self, key): return self.data.get(key)
        async def set(self, key, value): self.data[key] = value
    return MockRedis()
```

### 3. 参数化测试

```python
# ✅ 推荐：参数化
@pytest.mark.parametrize("event_type,expected", [
    ("view", 1),
    ("click", 2),
    ("purchase", 3),
])
async def test_event_types(event_type, expected):
    result = process_event_type(event_type)
    assert result == expected
```

---

## 代码质量检查清单

### FastAPI
- [ ] 所有路由都有 response_model
- [ ] 使用依赖注入管理数据库连接
- [ ] 异常通过全局处理器处理
- [ ] 使用 lifespan 管理资源生命周期

### 数据库
- [ ] 数据库查询使用预加载避免 N+1
- [ ] 批量操作使用 add_all
- [ ] 设置 expire_on_commit=False

### 缓存
- [ ] Redis 使用 Pipeline 批量操作
- [ ] 使用连接池管理连接

### 流处理
- [ ] Faust 使用 RocksDB 持久化状态
- [ ] Agent 正确处理异常
- [ ] 消息处理成功后再确认

### 性能
- [ ] 使用 orjson 进行 JSON 序列化
- [ ] 异步操作使用 asyncio.gather 并发
- [ ] 关键路径有缓存策略

### 质量
- [ ] 关键操作有日志记录
- [ ] 有单元测试覆盖
- [ ] 使用类型注解和 Pydantic 验证
