# 模块设计

## 模块概览

BehaviorSense 项目包含以下核心模块：

| 模块 | 技术栈 | 描述 |
|------|--------|------|
| behavior_core | Python | 核心数据模型与工具 |
| behavior_mock | FastAPI | 用户行为模拟器 |
| behavior_stream | PyFlink/Faust | 实时流处理 |
| behavior_rules | Python | 规则引擎服务 |
| behavior_insight | FastAPI | 洞察分析服务 |
| behavior_audit | FastAPI | 人工审核服务 |

---

## Core 模块

### 职责

核心数据模型、配置管理、公共工具。

### 数据模型

```python
# behavior_core/models/event.py
from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
import uuid


class EventType(str, Enum):
    """事件类型枚举"""
    VIEW = "view"
    CLICK = "click"
    SEARCH = "search"
    PURCHASE = "purchase"
    COMMENT = "comment"
    LOGIN = "login"
    LOGOUT = "logout"


class UserBehavior(BaseModel):
    """用户行为事件模型"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str | None = None
    page_url: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StandardEvent(BaseModel):
    """标准化事件模型"""
    event_id: str
    user_id: str
    event_type: str
    timestamp: datetime
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    properties: dict[str, Any]
    tags: list[str] = Field(default_factory=list)
```

### 配置管理

```python
# behavior_core/config/settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    # 应用
    app_name: str = "behavior-sense"
    debug: bool = False

    # Pulsar
    pulsar_url: str = "pulsar://localhost:6650"
    pulsar_tenant: str = "behavior-sense"
    pulsar_namespace: str = "default"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "behavior_sense"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # ClickHouse
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 9000

    class Config:
        env_file = ".env"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## Mock 模块

### 职责

生成模拟用户行为数据，用于测试和开发。

### 功能特性

- **多行为类型支持**: 浏览、点击、搜索、购买、评论、登录
- **可配置生成速率**: 每秒生成 N 条事件
- **场景模拟**: 支持促销活动、异常流量等场景
- **输出到 Pulsar**: 直接写入消息队列

### 核心实现

```python
# behavior_mock/generator.py
import random
import asyncio
from datetime import datetime
from typing import AsyncIterator
from behavior_core.models.event import UserBehavior, EventType


class BehaviorGenerator:
    """用户行为生成器"""

    def __init__(
        self,
        user_pool_size: int = 1000,
        event_types: list[EventType] | None = None,
    ):
        self.user_pool_size = user_pool_size
        self.event_types = event_types or list(EventType)
        self._pages = [
            "/home", "/product/123", "/product/456",
            "/cart", "/checkout", "/profile", "/search"
        ]

    def generate(self) -> UserBehavior:
        """生成单条行为"""
        user_id = f"user_{random.randint(1, self.user_pool_size)}"
        event_type = random.choice(self.event_types)

        properties = {}
        if event_type == EventType.VIEW:
            properties["page_url"] = random.choice(self._pages)
            properties["stay_duration"] = random.randint(5, 300)
        elif event_type == EventType.SEARCH:
            properties["keyword"] = f"keyword_{random.randint(1, 100)}"
            properties["result_count"] = random.randint(0, 100)
        elif event_type == EventType.PURCHASE:
            properties["product_id"] = f"prod_{random.randint(1, 500)}"
            properties["amount"] = round(random.uniform(10, 1000), 2)

        return UserBehavior(
            user_id=user_id,
            event_type=event_type,
            page_url=random.choice(self._pages) if random.random() > 0.3 else None,
            properties=properties,
        )

    def generate_batch(self, count: int) -> list[UserBehavior]:
        """批量生成"""
        return [self.generate() for _ in range(count)]

    async def stream(
        self,
        rate_per_second: int = 100,
    ) -> AsyncIterator[UserBehavior]:
        """流式生成"""
        interval = 1.0 / rate_per_second
        while True:
            yield self.generate()
            await asyncio.sleep(interval)
```

### Pulsar 生产者

```python
# behavior_mock/producer.py
import asyncio
import pulsar
import orjson
from behavior_core.models.event import UserBehavior


class PulsarProducer:
    """Pulsar 消息生产者"""

    def __init__(
        self,
        service_url: str = "pulsar://localhost:6650",
        topic: str = "persistent://behavior-sense/default/user-behavior",
    ):
        self.service_url = service_url
        self.topic = topic
        self._client: pulsar.Client | None = None
        self._producer: pulsar.Producer | None = None

    def connect(self) -> None:
        """建立连接"""
        self._client = pulsar.Client(self.service_url)
        self._producer = self._client.create_producer(
            self.topic,
            batching_enabled=True,
            batching_max_messages=1000,
            batching_max_publish_delay_ms=10,
        )

    def send(self, event: UserBehavior) -> None:
        """发送事件"""
        if self._producer is None:
            raise RuntimeError("Producer not connected")

        self._producer.send(
            orjson.dumps(event.model_dump()),
            event.event_id.encode(),
            event_timestamp=int(event.timestamp.timestamp() * 1000),
        )

    async def send_async(self, event: UserBehavior) -> None:
        """异步发送"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.send, event)

    def close(self) -> None:
        """关闭连接"""
        if self._producer:
            self._producer.close()
        if self._client:
            self._client.close()
```

### 事件类型

| 类型 | 描述 | 典型属性 |
|------|------|----------|
| VIEW | 页面浏览 | page_url, stay_duration |
| CLICK | 点击 | element_id, x, y |
| SEARCH | 搜索 | keyword, result_count |
| PURCHASE | 购买 | product_id, amount |
| COMMENT | 评论 | content, rating |
| LOGIN | 登录 | login_method, ip |
| LOGOUT | 登出 | - |

---

## Stream 模块

### 职责

实时处理用户行为数据流，进行聚合计算和模式识别。

### 方案一: Faust (纯 Python)

```python
# behavior_stream/app.py
import faust
from datetime import timedelta
from behavior_core.models.event import UserBehavior

app = faust.App(
    'behavior-sense',
    broker='pulsar://localhost:6650',
    store='rocksdb://',
    topic_replication_factor=1,
)

# 定义 Topic
behavior_topic = app.topic(
    'user-behavior',
    value_type=UserBehavior,
)

# 定义表 (状态存储)
user_stats = app.Table(
    'user_stats',
    default=dict,
    partitions=4,
)


@app.agent(behavior_topic)
async def process_events(events):
    """处理事件流"""
    async for event in events:
        # 更新用户统计
        stats = user_stats[event.user_id]
        stats['event_count'] = stats.get('event_count', 0) + 1
        stats['last_event'] = event.event_type
        stats['last_time'] = event.timestamp.isoformat()
        user_stats[event.user_id] = stats

        # 发送到规则引擎
        await rules_topic.send(value={
            'user_id': event.user_id,
            'stats': stats,
            'event': event.model_dump(),
        })


@app.timer(interval=60.0)
async def aggregate_minute():
    """每分钟聚合"""
    for user_id, stats in user_stats.items():
        if stats['event_count'] > 100:
            await alerts_topic.send(value={
                'user_id': user_id,
                'alert_type': 'high_activity',
                'count': stats['event_count'],
            })
```

### 方案二: PyFlink

```python
# behavior_stream/flink_job.py
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.window import TumblingEventTimeWindows
from pyflink.table import StreamTableEnvironment
from datetime import timedelta


def create_aggregation_job():
    """创建聚合任务"""
    env = StreamExecutionEnvironment.get_execution_environment()
    env.enable_checkpointing(60000)  # 每分钟检查点

    t_env = StreamTableEnvironment.create(env)

    # 创建 Pulsar 源表
    t_env.execute_sql("""
        CREATE TABLE user_behavior (
            event_id STRING,
            user_id STRING,
            event_type STRING,
            timestamp TIMESTAMP(3),
            properties STRING,
            WATERMARK FOR timestamp AS timestamp - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'pulsar',
            'topic' = 'persistent://behavior-sense/default/user-behavior',
            'service-url' = 'pulsar://localhost:6650',
            'format' = 'json'
        )
    """)

    # 窗口聚合
    result = t_env.sql_query("""
        SELECT
            user_id,
            TUMBLE_START(timestamp, INTERVAL '1' MINUTE) as window_start,
            TUMBLE_END(timestamp, INTERVAL '1' MINUTE) as window_end,
            COUNT(*) as event_count,
            COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) as purchase_count
        FROM user_behavior
        GROUP BY
            user_id,
            TUMBLE(timestamp, INTERVAL '1' MINUTE)
    """)

    # 输出到 Pulsar
    t_env.execute_sql("""
        CREATE TABLE aggregation_result (
            user_id STRING,
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            event_count BIGINT,
            purchase_count BIGINT
        ) WITH (
            'connector' = 'pulsar',
            'topic' = 'persistent://behavior-sense/default/aggregation-result',
            'service-url' = 'pulsar://localhost:6650',
            'format' = 'json'
        )
    """)

    result.execute_insert("aggregation_result")


if __name__ == "__main__":
    create_aggregation_job()
```

### 模式检测 (CEP)

```python
# behavior_stream/pattern.py
import faust
from collections import defaultdict
from datetime import datetime, timedelta

# 登录失败检测
login_fail_count = defaultdict(list)

@app.agent(behavior_topic)
async def detect_login_fail(events):
    """检测连续登录失败"""
    async for event in events:
        if event.event_type == 'login':
            if event.properties.get('status') == 'fail':
                user_fails = login_fail_count[event.user_id]
                user_fails.append(event.timestamp)

                # 清理过期记录
                cutoff = datetime.utcnow() - timedelta(minutes=10)
                login_fail_count[event.user_id] = [
                    t for t in user_fails if t > cutoff
                ]

                # 检测条件: 10分钟内失败5次
                if len(login_fail_count[event.user_id]) >= 5:
                    await alerts_topic.send(value={
                        'user_id': event.user_id,
                        'alert_type': 'login_fail_5times',
                        'count': len(login_fail_count[event.user_id]),
                    })
```

---

## Rules 模块

### 职责

规则定义、规则匹配、动作触发。

### 规则模型

```python
# behavior_rules/models.py
from pydantic import BaseModel
from typing import Any


class RuleAction(BaseModel):
    """规则动作"""
    type: str  # TAG_USER, TRIGGER_AUDIT, SEND_NOTIFICATION
    params: dict[str, Any] = {}


class Rule(BaseModel):
    """规则定义"""
    id: str
    name: str
    condition: str  # Python 表达式
    priority: int = 0
    enabled: bool = True
    actions: list[RuleAction] = []
```

### 规则引擎

```python
# behavior_rules/engine.py
from typing import Any, Callable
from behavior_rules.models import Rule, RuleAction


class RuleEngine:
    """规则引擎"""

    def __init__(self):
        self._rules: dict[str, Rule] = {}
        self._action_handlers: dict[str, Callable] = {}

    def register_rule(self, rule: Rule) -> None:
        """注册规则"""
        self._rules[rule.id] = rule

    def register_action_handler(
        self,
        action_type: str,
        handler: Callable[[dict[str, Any], dict[str, Any]], Any]
    ) -> None:
        """注册动作处理器"""
        self._action_handlers[action_type] = handler

    def evaluate(self, context: dict[str, Any]) -> list[Rule]:
        """评估所有规则，返回命中的规则"""
        matched = []
        for rule in sorted(
            self._rules.values(),
            key=lambda r: r.priority,
            reverse=True
        ):
            if rule.enabled and self._safe_eval(rule.condition, context):
                matched.append(rule)
        return matched

    def _safe_eval(self, condition: str, context: dict[str, Any]) -> bool:
        """安全地评估条件表达式"""
        try:
            # 限制可用的内置函数
            allowed_names = {
                "True": True,
                "False": False,
                "None": None,
            }
            return bool(eval(condition, {"__builtins__": {}}, {**allowed_names, **context}))
        except Exception:
            return False

    async def execute_actions(
        self,
        rules: list[Rule],
        context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """执行规则动作"""
        results = []
        for rule in rules:
            for action in rule.actions:
                handler = self._action_handlers.get(action.type)
                if handler:
                    try:
                        result = await handler(action.params, context)
                        results.append({
                            "rule_id": rule.id,
                            "action": action.type,
                            "result": result,
                        })
                    except Exception as e:
                        results.append({
                            "rule_id": rule.id,
                            "action": action.type,
                            "error": str(e),
                        })
        return results
```

### 规则示例

```yaml
# rules/high_value_user.yaml
id: high_value_user
name: 高价值用户
condition: purchase_count >= 5 and total_amount > 1000
priority: 1
enabled: true
actions:
  - type: TAG_USER
    params:
      tags: ["high_value", "vip"]
  - type: SEND_NOTIFICATION
    params:
      template: "vip_welcome"

---
# rules/login_risk.yaml
id: login_risk
name: 登录风险检测
condition: login_fail_count > 5
priority: 2
enabled: true
actions:
  - type: TRIGGER_AUDIT
    params:
      level: HIGH
      reason: "频繁登录失败"
  - type: TAG_USER
    params:
      tags: ["suspicious"]
```

### 动作处理器

```python
# behavior_rules/actions.py
from behavior_rules.engine import RuleEngine
import httpx


async def tag_user(params: dict, context: dict) -> dict:
    """打标签动作"""
    user_id = context["user_id"]
    tags = params["tags"]

    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"http://insight:8000/api/insight/user/{user_id}/tag",
            json={"tags": tags, "source": "rule"}
        )
    return {"status": response.status_code}


async def trigger_audit(params: dict, context: dict) -> dict:
    """触发审核动作"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://audit:8000/api/audit/order",
            json={
                "user_id": context["user_id"],
                "audit_level": params["level"],
                "trigger_data": context,
            }
        )
    return {"status": response.status_code}


# 注册处理器
engine = RuleEngine()
engine.register_action_handler("TAG_USER", tag_user)
engine.register_action_handler("TRIGGER_AUDIT", trigger_audit)
```

---

## Insight 模块

### 职责

标签管理、用户画像、分析报表。

### FastAPI 服务

```python
# behavior_insight/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import redis.asyncio as redis


class TagValue(BaseModel):
    value: str
    timestamp: datetime
    confidence: float = 1.0


class UserTags(BaseModel):
    user_id: str
    tags: dict[str, TagValue]
    last_update: datetime


class TagUpdate(BaseModel):
    tag_name: str
    tag_value: str
    source: str = "manual"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
    yield
    await app.state.redis.close()


app = FastAPI(title="BehaviorSense Insight", lifespan=lifespan)


@app.get("/api/insight/user/{user_id}/tags", response_model=UserTags)
async def get_user_tags(user_id: str) -> UserTags:
    """获取用户标签"""
    r: redis.Redis = app.state.redis
    tags_data = await r.hgetall(f"user:tags:{user_id}")

    if not tags_data:
        raise HTTPException(status_code=404, detail="User not found")

    tags = {
        name: TagValue(value=value, timestamp=datetime.utcnow())
        for name, value in tags_data.items()
    }

    return UserTags(
        user_id=user_id,
        tags=tags,
        last_update=datetime.utcnow(),
    )


@app.put("/api/insight/user/{user_id}/tag")
async def update_user_tag(user_id: str, update: TagUpdate):
    """更新用户标签"""
    r: redis.Redis = app.state.redis
    await r.hset(f"user:tags:{user_id}", update.tag_name, update.tag_value)
    await r.publish("tag:updates", f"{user_id}:{update.tag_name}:{update.tag_value}")
    return {"status": "ok"}
```

### 标签体系

```
标签分类
├── 基础属性标签
│   ├── 用户等级 (level)
│   ├── 注册时间 (register_time)
│   └── 地域分布 (region)
├── 行为特征标签
│   ├── 活跃度 (activity)
│   ├── 购买频次 (purchase_frequency)
│   └── 品类偏好 (category_preference)
├── 统计指标标签
│   ├── 最近7天浏览量 (view_7d)
│   ├── 最近30天消费额 (amount_30d)
│   └── 累计订单数 (order_count)
└── 预测标签
    ├── 流失风险 (churn_risk)
    ├── 复购概率 (repurchase_prob)
    └── 潜在价值 (potential_value)
```

---

## Audit 模块

### 职责

人工审核流程管理。

### 审核状态机

```
PENDING (待审核)
    │
    ▼
IN_REVIEW (审核中)
    │
    ├──▶ APPROVED (通过)
    │
    └──▶ REJECTED (驳回)
              │
              ▼
         CLOSED (已关闭)
```

### 审核服务

```python
# behavior_audit/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
import asyncpg


class AuditStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class AuditOrder(BaseModel):
    order_id: str
    user_id: str
    rule_id: str
    trigger_data: dict
    audit_level: str
    status: AuditStatus = AuditStatus.PENDING
    assignee: str | None = None
    reviewer_note: str | None = None
    create_time: datetime
    update_time: datetime


class ReviewRequest(BaseModel):
    status: AuditStatus
    reviewer_note: str | None = None


app = FastAPI(title="BehaviorSense Audit")


@app.post("/api/audit/order")
async def create_order(order: AuditOrder):
    """创建审核工单"""
    # 存储到数据库
    pass


@app.get("/api/audit/order/{order_id}")
async def get_order(order_id: str) -> AuditOrder:
    """获取审核详情"""
    pass


@app.put("/api/audit/order/{order_id}/review")
async def submit_review(order_id: str, review: ReviewRequest):
    """提交审核结果"""
    pass


@app.get("/api/audit/orders/todo")
async def get_todo_orders():
    """获取待办审核"""
    pass
```

---

## 模块间通信

### 消息队列主题

| 主题 | 生产者 | 消费者 | 描述 |
|------|--------|--------|------|
| user-behavior | Mock | Stream | 原始行为数据 |
| aggregation-result | Stream | Rules | 聚合结果 |
| rule-match-result | Rules | Insight/Audit | 规则匹配结果 |
| audit-result | Audit | Insight | 审核结果反馈 |
| tag-update | Insight | API | 标签更新通知 |

### 服务端口

| 服务 | 端口 |
|------|------|
| behavior_mock | 8001 |
| behavior_rules | 8002 |
| behavior_insight | 8003 |
| behavior_audit | 8004 |