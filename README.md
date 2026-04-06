# BehaviorSense

[![CI](https://github.com/afine907/behavior-sense/actions/workflows/ci.yml/badge.svg)](https://github.com/afine907/behavior-sense/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-orange.svg)](https://docs.astral.sh/ruff/)

**User Behavior Stream Analytics Engine** - A real-time user behavior stream processing and analysis platform.

[English](README.md) | [中文](README_CN.md)

---

## Overview

BehaviorSense is a real-time user behavior stream analytics engine designed for low-latency (< 1s) event processing, flexible rule matching, and intelligent user tagging.

### Key Features

- **Real-time Stream Processing** - Built on Faust for sub-second latency event processing
- **Flexible Rule Engine** - AST-based rule parsing with hot-reload support
- **Intelligent Tagging** - Automatic user profiling and tag management
- **Human-in-the-loop Audit** - Built-in workflow for manual review process
- **Monorepo Architecture** - Clean separation of concerns with shared libraries
- **Modern Python Stack** - FastAPI, Pydantic v2, asyncio throughout

### Architecture

```mermaid
flowchart TB
    subgraph DataIngestion["📡 数据入口层"]
        direction LR
        subgraph MockService["Mock 服务 :8001"]
            Generator["🎲 事件生成器\nBehaviorGenerator"]
            Scenarios["🎬 场景模拟\nNormal/FlashSale/Abnormal/Gradual"]
            Producer["📤 Pulsar 生产者"]
        end
        ExternalData["🌐 外部数据源"]
    end

    subgraph StreamProcessing["⚡ 流处理层"]
        subgraph Pulsar["Apache Pulsar :6650"]
            TopicEvents["📥 events Topic"]
            TopicAlerts["📤 alerts Topic"]
            TopicAgg["📊 aggregation Topic"]
        end
        subgraph StreamService["Stream 处理器"]
            Consumer["📥 事件消费者"]
            subgraph Aggregator["📐 聚合器"]
                WindowAgg["分钟窗口聚合"]
                UserStats["用户统计"]
            end
            subgraph Detector["🔍 检测器"]
                LoginFail["登录失败检测\n>5次/10分钟"]
                HighFreq["高频操作检测\n>100次/分钟"]
                RapidClick["快速点击检测\n>20次/10秒"]
                UnusualPurchase["异常购买检测\n>5次/小时"]
            end
            AlertSender["🚨 告警发送"]
        end
    end

    subgraph RuleEngine["🎯 规则引擎层 :8002"]
        subgraph RulesService["Rules 服务"]
            RuleCRUD["📋 规则管理\nCRUD API"]
            RuleLoader["📂 规则加载器\nYAML/DB"]
            subgraph Engine["⚙️ 规则引擎"]
                ASTParser["AST 解析器"]
                ConditionMatch["条件匹配"]
                PrioritySort["优先级排序"]
            end
            subgraph Actions["🎬 动作处理器"]
                TagAction["TAG_USER\n打标签"]
                AuditAction["TRIGGER_AUDIT\n触发审核"]
            end
        end
    end

    subgraph InsightLayer["📊 洞察分析层 :8003"]
        subgraph InsightService["Insight 服务"]
            TagService["🏷️ 标签服务"]
            UserProfile["👤 用户画像"]
            TagStats["📈 标签统计"]
        end
        Redis[("Redis\n:6379")]
        ClickHouse[("ClickHouse\n:8123")]
    end

    subgraph AuditLayer["✅ 人工审核层 :8004"]
        subgraph AuditService["Audit 服务"]
            OrderMgmt["📋 工单管理\n创建/查询/分配"]
            ReviewWorkflow["📝 审核流程\npending→in_review→approved/rejected"]
            AuditStats["📊 审核统计"]
        end
        PostgreSQL[("PostgreSQL\n:5432")]
    end

    subgraph Frontend["🖥️ 前端展示层 :5143"]
        NextJS["Next.js Web App"]
        subgraph Pages["页面"]
            Dashboard["Dashboard\n监控大盘"]
            RulesPage["Rules\n规则管理"]
            InsightPage["Insight\n用户洞察"]
            AuditPage["Audit\n审核中心"]
            MockPage["Mock\n事件模拟"]
        end
    end

    %% 数据流连接
    Generator --> Producer
    Scenarios --> Producer
    Producer --> TopicEvents
    ExternalData --> TopicEvents

    TopicEvents --> Consumer
    Consumer --> Aggregator
    Consumer --> Detector

    Aggregator --> WindowAgg
    WindowAgg --> UserStats
    UserStats --> TopicAgg

    Detector --> LoginFail
    Detector --> HighFreq
    Detector --> RapidClick
    Detector --> UnusualPurchase
    LoginFail --> AlertSender
    HighFreq --> AlertSender
    RapidClick --> AlertSender
    UnusualPurchase --> AlertSender
    AlertSender --> TopicAlerts

    TopicAlerts --> RuleCRUD
    TopicAgg --> RuleCRUD
    RuleLoader --> Engine
    RuleCRUD --> Engine
    Engine --> ASTParser
    ASTParser --> ConditionMatch
    ConditionMatch --> PrioritySort
    PrioritySort --> Actions
    Actions --> TagAction
    Actions --> AuditAction

    TagAction --> TagService
    TagService --> Redis
    TagService --> ClickHouse
    TagService --> UserProfile
    UserProfile --> TagStats

    AuditAction --> OrderMgmt
    OrderMgmt --> ReviewWorkflow
    ReviewWorkflow --> AuditStats
    OrderMgmt --> PostgreSQL

    NextJS --> Pages
    Dashboard --> |"实时监控"| StreamService
    RulesPage --> |"规则管理"| RuleCRUD
    InsightPage --> |"用户查询"| UserProfile
    AuditPage --> |"审核操作"| OrderMgmt
    MockPage --> |"事件生成"| Generator

    %% 样式
    classDef service fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef storage fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef detector fill:#fce4ec,stroke:#880e4f,stroke-width:1px
    classDef action fill:#e8f5e9,stroke:#1b5e20,stroke-width:1px

    class MockService,StreamService,RulesService,InsightService,AuditService service
    class Pulsar,Redis,PostgreSQL,ClickHouse storage
    class LoginFail,HighFreq,RapidClick,UnusualPurchase detector
    class TagAction,AuditAction action
```

#### 数据流说明

| 阶段 | 组件 | 功能 |
|------|------|------|
| **入口** | Mock/External | 生成测试事件或接收外部行为数据 |
| **传输** | Pulsar | 高吞吐消息队列，支持事件持久化 |
| **处理** | Stream | 实时聚合 + 异常模式检测 |
| **决策** | Rules | AST 规则引擎，支持热加载 |
| **洞察** | Insight | 用户画像 + 自动打标签 |
| **审核** | Audit | 人工介入处理高风险事件 |

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.11+ | Backend runtime |
| Package Manager | [uv](https://docs.astral.sh/uv/) | Python dependency management |
| Web Framework | FastAPI | REST API services |
| Frontend | Next.js 14 | Web application |
| Stream Processing | Faust | Real-time event processing |
| Message Queue | Apache Pulsar | Event streaming |
| Database | PostgreSQL | Persistent storage |
| Cache | Redis | Caching & pub/sub |
| Analytics | ClickHouse | OLAP queries |
| Search | Elasticsearch | Full-text search |
| Monitoring | Prometheus + Grafana | Metrics & visualization |

## Project Structure

```
behavior-sense/
├── libs/                     # Shared libraries
│   └── core/                 # behavior-core
│       └── src/behavior_core/
│           ├── config/       # Configuration management
│           ├── metrics/      # Prometheus metrics
│           ├── middleware/   # Rate limiting, tracing
│           ├── models/       # Data models
│           ├── security/     # Auth & JWT
│           └── utils/        # Utilities
│
├── packages/                 # Microservices
│   ├── mock/                 # behavior-mock (port 8001)
│   ├── rules/                # behavior-rules (port 8002)
│   ├── insight/              # behavior-insight (port 8003)
│   ├── audit/                # behavior-audit (port 8004)
│   └── stream/               # behavior-stream (Faust)
│
├── apps/                     # Frontend applications
│   └── web/                  # Next.js web app (port 5143)
│       └── src/
│           ├── app/          # Next.js app router
│           ├── components/   # React components
│           ├── lib/          # Utilities & API clients
│           └── types/        # TypeScript types
│
├── infrastructure/           # Infrastructure configs
│   └── docker/               # Dockerfile, docker-compose
│
├── tests/                    # Test suites
│   ├── test_api/             # API tests
│   ├── test_core/            # Core library tests
│   ├── test_integration/     # Integration tests
│   ├── test_mock/            # Mock service tests
│   ├── test_rules/           # Rules engine tests
│   ├── test_stream/          # Stream processor tests
│   ├── test_insight/         # Insight service tests
│   ├── test_audit/           # Audit service tests
│   └── performance/          # Locust performance tests
│
├── scripts/                  # Development scripts
└── wiki/                     # Documentation
```

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker & Docker Compose

### Installation

```bash
# Clone the repository
git clone https://github.com/afine907/behavior-sense.git
cd behavior-sense

# Install dependencies
uv sync

# Copy environment config
cp .env.example .env

# Start infrastructure services
docker-compose up -d
```

### Running Services

```bash
# Run mock service (generates test events)
uv run uvicorn behavior_mock.main:app --port 8001

# Run stream processor
uv run python -m behavior_stream

# Run insight API
uv run uvicorn behavior_insight.main:app --port 8003

# Run audit service
uv run uvicorn behavior_audit.main:app --port 8004
```

### Running Tests

The project uses a **dual-mode testing architecture** for fast iteration and production verification:

```bash
# Mock mode (fast, no external dependencies)
uv run pytest tests/test_api/test_mock_api.py tests/test_api/test_rules_api.py tests/test_integration/test_basic_integration.py -v

# Real dependencies mode (requires Docker)
docker-compose -f docker-compose.test.yml up -d
TEST_REAL_DEPS=1 uv run pytest tests/ -v
docker-compose -f docker-compose.test.yml down -v

# Run with coverage
uv run pytest tests/ --cov=libs --cov=packages --cov-report=html

# Using the test script
./scripts/run_tests.sh           # Mock mode
./scripts/run_tests.sh --real    # Real dependencies
./scripts/run_tests.sh --all     # All tests
```

| Mode | Dependencies | Use Case |
|------|--------------|----------|
| Mock | None | Fast iteration, local development |
| Real | Redis + PostgreSQL | CI verification, pre-production check |

For detailed test documentation, see [tests/test_api/TEST_REPORT.md](tests/test_api/TEST_REPORT.md).

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| behavior-mock | 8001 | Event generator |
| behavior-rules | 8002 | Rule engine API |
| behavior-insight | 8003 | User insight API |
| behavior-audit | 8004 | Audit workflow API |
| web | 5143 | Frontend web application |
| Pulsar | 6650 | Message queue |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache |
| ClickHouse | 8123 | Analytics |
| Elasticsearch | 9200 | Search engine |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Monitoring dashboard |

## API Documentation

Each service provides OpenAPI documentation:

- Mock: http://localhost:8001/docs
- Rules: http://localhost:8002/docs
- Insight: http://localhost:8003/docs
- Audit: http://localhost:8004/docs
- Web: http://localhost:5143

## Development

### Adding Dependencies

```bash
# Add to root project
uv add httpx

# Add to specific package
uv add --package behavior-audit httpx

# Add dev dependency
uv add --group dev black
```

### Code Quality

```bash
# Lint
uv run ruff check libs/ packages/

# Format
uv run ruff format libs/ packages/

# Type check
uv run mypy libs/core/src packages/*/src
```

### Docker Build

```bash
# Build specific service
docker build -f infrastructure/docker/Dockerfile --build-arg SERVICE=insight -t behaviorsense/insight:latest .
```

## Documentation

- [Architecture Design](wiki/architecture.md)
- [Module Design](wiki/modules.md)
- [Technology Stack](wiki/technology.md)
- [API Design](wiki/api.md)
- [Deployment Guide](wiki/deployment.md)
- [Best Practices](wiki/best-practices.md)
- [Development Plan](PLAN.md)

## Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes using [Conventional Commits](https://www.conventionalcommits.org/)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Convention

All commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

# Examples
feat(audit): add audit state machine for review workflow
fix(rules): prevent eval injection with AST parser
docs(api): update endpoint documentation
test(core): add unit tests for models
refactor: migrate to monorepo structure
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
