# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BehaviorSense is an AI Agent behavior analytics platform built with Python 3.11+ using a monorepo architecture. It captures, processes, and analyzes AI agent interactions in real-time, enabling observability, performance optimization, and behavioral insights for autonomous agent systems.

## Commands

### Package Management (uv)

```bash
uv sync                           # Install all dependencies
uv add httpx                      # Add dependency to root
uv add --package behavior-audit httpx  # Add to specific package
uv run <command>                  # Run any command with virtual environment
```

### Development

```bash
# Run services
uv run uvicorn behavior_collector.main:app --port 8001
uv run uvicorn behavior_rules.main:app --port 8002
uv run uvicorn behavior_insight.main:app --port 8003
uv run uvicorn behavior_audit.main:app --port 8004
uv run uvicorn behavior_traces.main:app --port 8005
uv run uvicorn behavior_metrics.main:app --port 8006
uv run python -m behavior_stream  # Faust stream processor

# Code quality
uv run ruff check libs/ packages/
uv run ruff format libs/ packages/
uv run mypy libs/core/src/behavior_core --ignore-missing-imports
uv run mypy packages/*/src --ignore-missing-imports
```

### Testing

```bash
# Fast tests (no external dependencies)
uv run pytest tests/test_api/test_collector_api.py tests/test_api/test_rules_api.py tests/test_integration/test_basic_integration.py -v

# Agent-specific tests
uv run pytest tests/test_agents/ -v
uv run pytest tests/test_api/test_traces_api.py tests/test_api/test_metrics_api.py -v

# Full tests with real dependencies (requires Docker)
TEST_REAL_DEPS=1 uv run pytest tests/ --cov=libs --cov=packages -v

# Or use the scripts
./scripts/run_tests.sh           # Mock mode
./scripts/run_tests.sh --real    # Real dependencies
```

## Architecture

### Data Flow

```
Agents → Collector (port 8001) → Pulsar (port 6650) → Stream (Faust) → Rules (port 8002) → Insight (port 8003)
                                            ↓              ↓                ↓
                                       Agent Traces   Agent Metrics    Audit (port 8004)
                                       (port 8005)    (port 8006)
```

### Monorepo Structure

```
libs/core/           # Shared library: config, models, security, middleware, utils
packages/collector/  # Agent event collector (FastAPI)
packages/stream/     # Real-time stream processing (Faust)
packages/rules/      # Rule engine API (FastAPI)
packages/insight/    # Agent insight/tagging API (FastAPI)
packages/audit/      # Manual review workflow (FastAPI)
packages/traces/     # Agent trace analysis (FastAPI)
packages/metrics/    # Agent performance metrics (FastAPI)
apps/web/            # Frontend (Next.js, reserved)
tests/               # test_api/, test_integration/, test_core/, test_agents/, etc.
```

### Module Responsibilities

| Module | Tech | Port | Purpose |
|--------|------|------|---------|
| collector | FastAPI | 8001 | Agent event ingestion and validation |
| stream | Faust | - | Real-time event processing, aggregation, pattern detection |
| rules | FastAPI | 8002 | Rule matching engine with hot-reload |
| insight | FastAPI | 8003 | Agent profiling and tag management |
| audit | FastAPI | 8004 | Human-in-the-loop review workflow |
| traces | FastAPI | 8005 | Agent trace analysis and debugging |
| metrics | FastAPI | 8006 | Agent performance metrics and monitoring |

### Shared Library (libs/core)

- `config/` - Settings using pydantic-settings
- `models/` - Pydantic v2 data models (including agent-specific models)
- `security/` - JWT auth, password hashing
- `middleware/` - Rate limiting, request tracing
- `utils/` - Logging (structlog), datetime utilities

### AI Agent Analytics Features

- **Agent Traces**: Capture and analyze agent execution traces, tool calls, and decision chains
- **Agent Metrics**: Performance monitoring including latency, token usage, and success rates
- **Behavioral Patterns**: Detect anomalous agent behaviors and optimization opportunities
- **Tool Usage Analysis**: Track and analyze tool call patterns and efficiency
- **Cost Optimization**: Monitor and optimize token consumption and API call patterns

## Code Conventions

### Commit Messages

All commits must follow [Conventional Commits](https://www.conventionalcommits.org/) in **English**:

```
feat(audit): add audit state machine for review workflow
fix(rules): prevent eval injection with AST parser
docs(api): update endpoint documentation
test(core): add unit tests for models
refactor: migrate to monorepo structure
feat(traces): add agent trace analysis endpoint
feat(metrics): add token usage tracking for agents
fix(collector): validate agent event payloads
```

### Code Style

- Line length: 100 characters
- Linter: ruff with rules E, F, I, N, W, UP, B, C4
- Type hints: Required for `behavior_core.*` (strict mode), optional for packages

### Python Best Practices

- Use dependency injection for database sessions in FastAPI
- Use `asyncio.gather()` for concurrent operations
- Use `orjson` for JSON serialization (3-5x faster than stdlib json)
- Use SQLAlchemy `selectinload` to avoid N+1 queries
- Set `expire_on_commit=False` for async sessions

## Technology Stack

| Layer | Technology |
|-------|------------|
| Runtime | Python 3.11+ |
| Package Manager | uv |
| Web Framework | FastAPI |
| Validation | Pydantic v2 |
| Stream Processing | Faust |
| Message Queue | Apache Pulsar |
| Database | PostgreSQL + SQLAlchemy async |
| Cache | Redis |
| Analytics | ClickHouse |
| Logging | structlog |
| Agent Tracing | OpenTelemetry |
| Metrics Collection | Prometheus |

## Key Files

- `pyproject.toml` - Root config, uv workspace, ruff/mypy settings
- `wiki/architecture.md` - System architecture diagrams
- `wiki/best-practices.md` - FastAPI, Pydantic, SQLAlchemy, Faust best practices
- `tests/test_api/TEST_REPORT.md` - Test documentation

## CI/CD

The project uses GitHub Actions (`.github/workflows/ci.yml`) with:
1. **lint**: ruff check + mypy
2. **test-mock**: Fast tests without external dependencies
3. **test-integration**: Full tests with PostgreSQL and Redis containers
4. **build**: Docker images for each service (on main/master only)

## Infrastructure

- Docker Compose: `docker-compose.yml` and `docker-compose.test.yml`
- Dockerfile: `infrastructure/docker/Dockerfile` (multi-service build)
