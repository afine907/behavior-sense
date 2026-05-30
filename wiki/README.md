# BehaviorSense Wiki

Welcome to the BehaviorSense project documentation.

## Table of Contents

- [Architecture Design](architecture.md) - System architecture and design principles
- [Module Design](modules.md) - Detailed design of all modules
- [Technology Stack](technology.md) - Tech choices and version recommendations
- [API Design](api.md) - RESTful API specifications
- [Deployment Guide](deployment.md) - Environment setup and deployment
- [Best Practices](best-practices.md) - Coding standards and patterns

---

## Project Overview

**BehaviorSense** - Real-time AI Agent Behavior Analytics Platform

An open-source platform for monitoring, analyzing, and governing AI Agent behavior in real-time with 12 anomaly detectors.

### Data Flow

```
Agent Action → Pulsar → Stream Processing → Detection → Auto-tag / Audit
     ↓              < 1 second           ↓
  [Events] ────→ [12 Detectors] ────→ [Decision] ────→ [Action]
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Package Manager | uv |
| Web Framework | FastAPI |
| Stream Processing | Pulsar Client |
| Message Queue | Apache Pulsar |
| Database | PostgreSQL |
| Cache | Redis |
| Analytics | ClickHouse |
| Frontend | Next.js 14 |

---

## Project Structure

```
behavior-sense/
├── libs/                     # Shared libraries
│   ├── core/                 # behavior-core (models, config, security)
│   ├── sdk/                  # Python SDK client
│   └── integrations/         # Framework integrations
│       ├── langchain/        # LangChain callback
│       ├── llamaindex/       # LlamaIndex callback
│       └── openai/           # OpenAI wrapper
│
├── packages/                 # Microservices
│   ├── mock/                 # Agent event generator (:8001)
│   ├── stream/               # Real-time stream processor
│   │   └── agent_detectors.py  # 12 anomaly detectors
│   ├── rules/                # Rule engine (:8002)
│   ├── insight/              # Agent analytics (:8003)
│   ├── audit/                # Audit workflow (:8004)
│   └── logs/                 # Event logs (:8005)
│
├── apps/                     # Frontend apps
│   └── web/                  # Next.js dashboard (:5143)
│
├── infrastructure/           # Infrastructure configs
│   └── docker/
│
├── tests/                    # Test suites
├── docs/                     # Documentation
├── examples/                 # SDK usage examples
└── wiki/                     # This wiki
```

---

## Quick Start

```bash
# Install dependencies
uv sync

# Start infrastructure
docker-compose up -d

# Run mock service
uv run uvicorn behavior_mock.main:app --port 8001

# Run stream processor
uv run python -m behavior_stream

# Run insight API
uv run uvicorn behavior_insight.main:app --port 8003

# Run tests
uv run pytest tests/
```

---

## Core Features

1. **Mock** - Generate simulated AI Agent events with 5 profiles
2. **Stream** - Real-time processing with 12 anomaly detectors
3. **Rules** - AST-safe rule engine with hot-reload
4. **Insight** - Agent profiling, stats, and graph analysis
5. **Audit** - Human-in-the-loop review workflow
6. **Logs** - Event log retrieval and trace analysis

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Apache Pulsar](https://pulsar.apache.org/)
- [ClickHouse](https://clickhouse.com/)
- [uv Package Manager](https://docs.astral.sh/uv/)
- [Next.js](https://nextjs.org/)
