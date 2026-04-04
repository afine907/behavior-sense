# Architecture Design

## Overview

BehaviorSense adopts a **monorepo** architecture with clear separation of concerns between shared libraries, microservices, and frontend applications.

## Directory Structure

```
behavior-sense/
├── libs/                     # Shared libraries (Python)
│   └── core/                 # behavior-core
│       ├── pyproject.toml
│       └── src/behavior_core/
│           ├── config/       # Configuration management
│           ├── models/       # Data models (Pydantic)
│           ├── security/     # Auth, JWT, password hashing
│           ├── middleware/   # Rate limiting, tracing
│           ├── metrics/      # Prometheus metrics
│           └── utils/        # Logging, datetime utilities
│
├── packages/                 # Python microservices
│   ├── audit/                # behavior-audit (port 8004)
│   │   ├── pyproject.toml
│   │   └── src/behavior_audit/
│   ├── insight/              # behavior-insight (port 8003)
│   ├── mock/                 # behavior-mock (port 8001)
│   ├── rules/                # behavior-rules (port 8002)
│   └── stream/               # behavior-stream (Faust)
│
├── apps/                     # Frontend applications
│   └── web/                  # Next.js app (reserved)
│
├── infrastructure/           # Infrastructure configs
│   └── docker/               # Dockerfile, docker-compose
│
├── tests/                    # Test suites
│   ├── test_core/
│   ├── test_audit/
│   ├── test_insight/
│   ├── test_mock/
│   ├── test_rules/
│   └── test_stream/
│
└── wiki/                     # Documentation
```

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            BehaviorSense                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌────────┐│
│   │  Mock   │───▶│ Pulsar  │───▶│  Stream │───▶│  Rules  │───▶│ Insight││
│   │ FastAPI │    │  Queue   │    │  Faust  │    │ Engine  │    │ FastAPI││
│   │ :8001   │    │  :6650   │    │  (async) │    │  :8002  │    │ :8003  ││
│   └─────────┘    └─────────┘    └─────────┘    └─────────┘    └────────┘│
│        │                                                        │        │
│        │              ┌─────────────────────────────────────────┘        │
│        │              ▼                                                  │
│        │       ┌─────────────┐                                          │
│        └──────▶│   Audit     │◀──────── Human Review Workflow           │
│                │   FastAPI   │                                          │
│                │   :8004     │                                          │
│                └─────────────┘                                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Technology Layers                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                Application Layer (FastAPI)                   │   │
│   │   packages/mock  │  packages/rules  │  packages/insight      │   │
│   │   packages/audit │  libs/core       │  packages/stream       │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                        │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                Stream Processing (Faust)                     │   │
│   │   Window Aggregation  │  Pattern Detection  │  CEP          │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                        │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                Message Layer (Apache Pulsar)                 │   │
│   │   Topics  │  Partitions  │  Persistence  │  Subscriptions   │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                        │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                Storage Layer                                 │   │
│   │   PostgreSQL  │  Redis  │  ClickHouse  │  Elasticsearch    │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
User Behavior Events
        │
        ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Mock     │────▶│   Pulsar    │────▶│   Stream    │────▶│    Rules    │
│  Generator  │     │    Topic    │     │   Faust     │     │   Engine    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                  │
                                                                  ▼
                                                        ┌─────────────┐
                                                        │   Insight   │
                                                        │  Tag/Profile│
                                                        └─────────────┘
                                                                  │
                                                                  ▼
                                                        ┌─────────────┐
                                                        │    Audit    │
                                                        │ Manual Review│
                                                        └─────────────┘
```

## Module Responsibilities

| Module | Tech | Responsibility | Input | Output |
|--------|------|----------------|-------|--------|
| libs/core | Python | Shared models, config, utils | - | - |
| packages/mock | FastAPI | Generate test events | Config | UserBehavior events |
| packages/stream | Faust | Stream processing | Events | Aggregations, patterns |
| packages/rules | FastAPI | Rule matching | Aggregations | Rule triggers |
| packages/insight | FastAPI | User profiling | Triggers | Tags, profiles |
| packages/audit | FastAPI | Manual review | Review tasks | Audit results |

## Design Principles

### 1. Monorepo with Workspace

- **uv workspace** for Python dependency management
- **pnpm workspace** for frontend (reserved)
- Shared code in `libs/`, services in `packages/`

### 2. Async-First

```python
# Async throughout
async def process_events():
    async for event in event_stream():
        await process_event(event)
        await update_tags(event.user_id)
```

### 3. Stream Processing

- Real-time event processing with latency < 1s
- Event-time processing with Faust
- Stateful processing with RocksDB

### 4. Rule-Compute Separation

- Stream handles aggregation and pattern detection
- Rules engine focuses on business logic
- Hot-reload rules without restart

## Scalability

### Horizontal Scaling

| Component | Scaling Strategy |
|-----------|------------------|
| Pulsar | Add partitions |
| Faust | Increase parallelism |
| FastAPI | Add instances behind load balancer |
| PostgreSQL | Read replicas |
| Redis | Cluster mode |

### Vertical Scaling

- Increase uvicorn workers
- Increase memory for Faust state
- Increase connection pool sizes

## Fault Tolerance

### Message Persistence

- Pulsar persistent topics with replication
- Acknowledgment mechanism for consumers
- Dead letter queue for failed messages

### Checkpointing

```python
# Faust checkpoint configuration
app = faust.App(
    'behavior-sense',
    broker='pulsar://localhost:6650',
    store='rocksdb://',
    table_standby_replicas=2,
    topic_replication_factor=3,
)
```

## Monitoring

### Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| end_to_end_latency | End-to-end delay | > 5s |
| processing_time | Event processing time | > 1s |
| rule_match_time | Rule matching time | > 100ms |
| pulsar_backlog | Message backlog | > 100k |

### Prometheus Integration

```python
from behavior_core.metrics import get_metrics

metrics = get_metrics()
metrics.increment('events_processed', tags={'type': 'view'})
```

## Security

- JWT authentication in `libs/core/security/`
- Rate limiting middleware
- TraceID for request tracing
- SecretStr for sensitive config
