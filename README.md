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
    subgraph DataIngestion["📡 Data Ingestion Layer"]
        direction LR
        subgraph MockService["Mock Service :8001"]
            Generator["🎲 Event Generator\nBehaviorGenerator"]
            Scenarios["🎬 Scenario Simulation\nNormal/FlashSale/Abnormal/Gradual"]
            Producer["📤 Pulsar Producer"]
        end
        ExternalData["🌐 External Data Sources"]
    end

    subgraph StreamProcessing["⚡ Stream Processing Layer"]
        subgraph Pulsar["Apache Pulsar :6650"]
            TopicEvents["📥 events Topic"]
            TopicAlerts["📤 alerts Topic"]
            TopicAgg["📊 aggregation Topic"]
        end
        subgraph StreamService["Stream Processor"]
            Consumer["📥 Event Consumer"]
            subgraph Aggregator["📐 Aggregator"]
                WindowAgg["Minute Window Aggregation"]
                UserStats["User Statistics"]
            end
            subgraph Detector["🔍 Detectors"]
                LoginFail["Login Failure Detection\n>5 fails/10min"]
                HighFreq["High Frequency Detection\n>100 events/min"]
                RapidClick["Rapid Click Detection\n>20 clicks/10s"]
                UnusualPurchase["Unusual Purchase Detection\n>5 purchases/hour"]
            end
            AlertSender["🚨 Alert Sender"]
        end
    end

    subgraph RuleEngine["🎯 Rule Engine Layer :8002"]
        subgraph RulesService["Rules Service"]
            RuleCRUD["📋 Rule Management\nCRUD API"]
            RuleLoader["📂 Rule Loader\nYAML/DB"]
            subgraph Engine["⚙️ Rule Engine"]
                ASTParser["AST Parser"]
                ConditionMatch["Condition Matching"]
                PrioritySort["Priority Sorting"]
            end
            subgraph Actions["🎬 Action Handlers"]
                TagAction["TAG_USER\nTag User"]
                AuditAction["TRIGGER_AUDIT\nTrigger Audit"]
            end
        end
    end

    subgraph InsightLayer["📊 Insight Analytics Layer :8003"]
        subgraph InsightService["Insight Service"]
            TagService["🏷️ Tag Service"]
            UserProfile["👤 User Profile"]
            TagStats["📈 Tag Statistics"]
        end
        Redis[("Redis\n:6379")]
        ClickHouse[("ClickHouse\n:8123")]
    end

    subgraph AuditLayer["✅ Manual Audit Layer :8004"]
        subgraph AuditService["Audit Service"]
            OrderMgmt["📋 Order Management\nCreate/Query/Assign"]
            ReviewWorkflow["📝 Review Workflow\npending→in_review→approved/rejected"]
            AuditStats["📊 Audit Statistics"]
        end
        PostgreSQL[("PostgreSQL\n:5432")]
    end

    subgraph Frontend["🖥️ Frontend Layer :5143"]
        NextJS["Next.js Web App"]
        subgraph Pages["Pages"]
            Dashboard["Dashboard\nMonitoring"]
            RulesPage["Rules\nManagement"]
            InsightPage["Insight\nUser Analytics"]
            AuditPage["Audit\nReview Center"]
            MockPage["Mock\nEvent Simulation"]
        end
    end

    %% Data Flow Connections
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
    Dashboard --> |"Real-time Monitor"| StreamService
    RulesPage --> |"Rule Management"| RuleCRUD
    InsightPage --> |"User Query"| UserProfile
    AuditPage --> |"Audit Operations"| OrderMgmt
    MockPage --> |"Event Generation"| Generator

    %% Styles
    classDef service fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef storage fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef detector fill:#fce4ec,stroke:#880e4f,stroke-width:1px
    classDef action fill:#e8f5e9,stroke:#1b5e20,stroke-width:1px

    class MockService,StreamService,RulesService,InsightService,AuditService service
    class Pulsar,Redis,PostgreSQL,ClickHouse storage
    class LoginFail,HighFreq,RapidClick,UnusualPurchase detector
    class TagAction,AuditAction action
```

#### Data Flow Description

| Stage | Component | Function |
|-------|-----------|----------|
| **Ingestion** | Mock/External | Generate test events or receive external behavior data |
| **Transport** | Pulsar | High-throughput message queue with event persistence |
| **Processing** | Stream | Real-time aggregation + anomaly pattern detection |
| **Decision** | Rules | AST-based rule engine with hot-reload support |
| **Insight** | Insight | User profiling + automatic tagging |
| **Audit** | Audit | Human-in-the-loop for high-risk events |

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
