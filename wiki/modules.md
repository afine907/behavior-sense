# Module Design

## Module Overview

| Module | Path | Tech | Port | Description |
|--------|------|------|------|-------------|
| behavior-core | `libs/core/` | Python | - | Shared library |
| behavior-mock | `packages/mock/` | FastAPI | 8001 | Event generator |
| behavior-stream | `packages/stream/` | Faust | - | Stream processor |
| behavior-rules | `packages/rules/` | FastAPI | 8002 | Rule engine |
| behavior-insight | `packages/insight/` | FastAPI | 8003 | User insight |
| behavior-audit | `packages/audit/` | FastAPI | 8004 | Audit workflow |

---

## Core Module (`libs/core/`)

### Responsibility

Shared data models, configuration, security, and utilities.

### Structure

```
libs/core/
├── pyproject.toml
└── src/behavior_core/
    ├── __init__.py
    ├── config/
    │   ├── __init__.py
    │   └── settings.py      # Pydantic Settings
    ├── models/
    │   ├── __init__.py
    │   ├── event.py         # UserBehavior, EventType
    │   └── user.py          # UserProfile, UserTags
    ├── security/
    │   ├── __init__.py
    │   ├── auth.py          # Password hashing
    │   └── jwt.py           # JWT token handling
    ├── middleware/
    │   ├── __init__.py
    │   ├── rate_limit.py    # API rate limiting
    │   └── tracing.py       # TraceID middleware
    ├── metrics.py           # Prometheus metrics
    └── utils/
        ├── __init__.py
        ├── datetime.py      # Timezone-aware datetime
        └── logging.py       # Structlog setup
```

### Data Models

```python
# libs/core/src/behavior_core/models/event.py
from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
import uuid


class EventType(str, Enum):
    VIEW = "view"
    CLICK = "click"
    SEARCH = "search"
    PURCHASE = "purchase"
    COMMENT = "comment"
    LOGIN = "login"
    LOGOUT = "logout"


class UserBehavior(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str | None = None
    page_url: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
```

### Configuration

```python
# libs/core/src/behavior_core/config/settings.py
from pydantic_settings import BaseSettings
from pydantic import SecretStr


class Settings(BaseSettings):
    # Application
    app_name: str = "behavior-sense"
    debug: bool = False

    # Services
    pulsar_url: str = "pulsar://localhost:6650"
    redis_url: str = "redis://localhost:6379"

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: SecretStr = SecretStr("postgres")
    postgres_db: str = "behavior_sense"

    # Security
    jwt_secret: SecretStr = SecretStr("change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
```

---

## Mock Module (`packages/mock/`)

### Responsibility

Generate simulated user behavior events for testing and development.

### Structure

```
packages/mock/
├── pyproject.toml
└── src/behavior_mock/
    ├── __init__.py
    ├── main.py              # FastAPI app
    ├── generator.py         # Event generator
    ├── producer.py          # Pulsar producer
    └── scenarios.py         # Predefined scenarios
```

### Event Types

| Type | Description | Properties |
|------|-------------|------------|
| VIEW | Page view | page_url, stay_duration |
| CLICK | Click event | element_id, x, y |
| SEARCH | Search query | keyword, result_count |
| PURCHASE | Purchase | product_id, amount |
| COMMENT | Comment | content, rating |
| LOGIN | Login attempt | method, status |
| LOGOUT | Logout | - |

---

## Stream Module (`packages/stream/`)

### Responsibility

Real-time event stream processing with Faust.

### Structure

```
packages/stream/
├── pyproject.toml
└── src/behavior_stream/
    ├── __init__.py
    ├── main.py              # Entry point
    ├── app.py               # Faust app definition
    ├── jobs/
    │   ├── __init__.py
    │   ├── aggregation.py   # Window aggregation
    │   └── detection.py     # Pattern detection
    └── operators/
        ├── __init__.py
        └── window.py        # Custom window functions
```

### Faust Application

```python
# packages/stream/src/behavior_stream/app.py
import faust

app = faust.App(
    'behavior-sense',
    broker='pulsar://localhost:6650',
    store='rocksdb://',
    topic_replication_factor=1,
)

behavior_topic = app.topic('user-behavior', value_type=dict)
user_stats = app.Table('user_stats', default=dict, partitions=4)
```

---

## Rules Module (`packages/rules/`)

### Responsibility

Rule definition, matching, and action execution.

### Structure

```
packages/rules/
├── pyproject.toml
└── src/behavior_rules/
    ├── __init__.py
    ├── main.py              # FastAPI app
    ├── engine.py            # Rule engine (AST-based)
    ├── loader.py            # YAML rule loader
    ├── models.py            # Rule models
    └── actions/
        ├── __init__.py
        ├── tagging.py       # Tag user action
        └── audit.py         # Trigger audit action
```

### Rule Definition

```yaml
# rules/high_value_user.yaml
id: high_value_user
name: High Value User
condition: purchase_count >= 5 and total_amount > 1000
priority: 1
enabled: true
actions:
  - type: TAG_USER
    params:
      tags: ["high_value", "vip"]
```

### Safe Evaluation

The rule engine uses AST parsing instead of `eval()` for security:

```python
# packages/stream/src/behavior_rules/engine.py
import ast

class RuleEngine:
    def _safe_eval(self, condition: str, context: dict) -> bool:
        """Safely evaluate condition using AST parsing"""
        tree = ast.parse(condition, mode='eval')
        # Only allow safe operations
        return self._eval_node(tree.body, context)
```

---

## Insight Module (`packages/insight/`)

### Responsibility

User profiling and tag management.

### Structure

```
packages/insight/
├── pyproject.toml
└── src/behavior_insight/
    ├── __init__.py
    ├── main.py              # FastAPI app
    ├── routers/
    │   ├── __init__.py
    │   ├── profile.py       # User profile API
    │   └── tags.py          # Tag management API
    ├── services/
    │   ├── __init__.py
    │   └── tag_service.py   # Tag business logic
    └── repositories/
        ├── __init__.py
        └── user_repo.py     # Database operations
```

### Tag Hierarchy

```
Tags
├── Demographics
│   ├── level (user level)
│   ├── region (geo location)
│   └── register_time
├── Behavior
│   ├── activity (activity level)
│   ├── purchase_frequency
│   └── category_preference
├── Metrics
│   ├── view_7d (7-day views)
│   ├── amount_30d (30-day spend)
│   └── order_count
└── Predictions
    ├── churn_risk
    ├── repurchase_prob
    └── potential_value
```

---

## Audit Module (`packages/audit/`)

### Responsibility

Manual review workflow management.

### Structure

```
packages/audit/
├── pyproject.toml
└── src/behavior_audit/
    ├── __init__.py
    ├── main.py              # FastAPI app
    ├── routers/
    │   ├── __init__.py
    │   └── audit.py         # Audit API
    ├── services/
    │   ├── __init__.py
    │   └── audit_service.py # State machine
    └── repositories/
        ├── __init__.py
        └── audit_repo.py    # Database operations
```

### Audit State Machine

```
PENDING ──────▶ IN_REVIEW ──────▶ APPROVED
                   │
                   └────────────▶ REJECTED
                                      │
                                      ▼
                                  CLOSED
```

---

## Inter-Module Communication

### Message Topics

| Topic | Producer | Consumer | Description |
|-------|----------|----------|-------------|
| user-behavior | mock | stream | Raw events |
| aggregation-result | stream | rules | Aggregations |
| rule-match-result | rules | insight/audit | Triggers |
| audit-result | audit | insight | Review results |

### Service Discovery

Services communicate via HTTP using service names:

```python
# Inside rules module
async def trigger_tag(user_id: str, tags: list[str]):
    async with httpx.AsyncClient() as client:
        await client.put(
            f"http://insight:8003/api/insight/user/{user_id}/tag",
            json={"tags": tags, "source": "rule"}
        )
```
