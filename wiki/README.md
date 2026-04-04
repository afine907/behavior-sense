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

**BehaviorSense** - User Behavior Stream Analytics Engine

A real-time user behavior stream processing and analysis platform with sub-second latency.

### Data Flow

```
Mock → Pulsar → Faust(Stream) → Rules → Insight
                                     ↓
                                  Audit (Manual Review)
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Package Manager | uv |
| Web Framework | FastAPI |
| Stream Processing | Faust |
| Message Queue | Apache Pulsar |
| Database | PostgreSQL |
| Cache | Redis |
| Analytics | ClickHouse |

---

## Project Structure

```
behavior-sense/
├── libs/                     # Shared libraries
│   └── core/                 # behavior-core
│       └── src/behavior_core/
│
├── packages/                 # Microservices
│   ├── audit/                # behavior-audit (:8004)
│   ├── insight/              # behavior-insight (:8003)
│   ├── mock/                 # behavior-mock (:8001)
│   ├── rules/                # behavior-rules (:8002)
│   └── stream/               # behavior-stream (Faust)
│
├── apps/                     # Frontend apps (reserved)
│   └── web/                  # Next.js
│
├── infrastructure/           # Infrastructure configs
│   └── docker/
│
├── tests/                    # Test suites
└── wiki/                     # Documentation
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

1. **Mock** - Generate simulated user behavior events
2. **Stream** - Real-time event processing with Faust
3. **Rules** - Flexible rule engine with AST parsing
4. **Insight** - User profiling and tag management
5. **Audit** - Manual review workflow

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Apache Pulsar](https://pulsar.apache.org/)
- [Faust Stream Processing](https://faust-streaming.github.io/faust/)
- [uv Package Manager](https://docs.astral.sh/uv/)
