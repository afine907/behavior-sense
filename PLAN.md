# BehaviorSense Development Plan

## Project Overview

Multi-agent parallel development of BehaviorSense - a real-time user behavior stream analytics engine.

## Monorepo Structure

```
behavior-sense/
├── pyproject.toml           # Root config + uv workspace
├── uv.lock                   # Lock file
├── pnpm-workspace.yaml       # Frontend workspace (reserved)
│
├── libs/                     # Shared libraries
│   └── core/                 # behavior-core
│       ├── pyproject.toml
│       └── src/behavior_core/
│           ├── config/
│           ├── models/
│           ├── security/
│           ├── middleware/
│           ├── metrics.py
│           └── utils/
│
├── packages/                 # Microservices
│   ├── audit/                # behavior-audit (:8004)
│   │   ├── pyproject.toml
│   │   └── src/behavior_audit/
│   ├── insight/              # behavior-insight (:8003)
│   ├── mock/                 # behavior-mock (:8001)
│   ├── rules/                # behavior-rules (:8002)
│   └── stream/               # behavior-stream (Faust)
│
├── apps/                     # Frontend applications
│   └── web/                  # Next.js (reserved)
│
├── infrastructure/           # Infrastructure configs
│   └── docker/
│
└── tests/                    # Test suites
    ├── test_core/
    ├── test_audit/
    ├── test_insight/
    ├── test_mock/
    ├── test_rules/
    └── test_stream/
```

---

## Task Dependency Graph

```
                    ┌─────────────┐
                    │ Phase 0     │
                    │ Project     │
                    │ Init        │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Phase 1     │
                    │ libs/core   │
                    │ (Shared Lib)│
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
   │ Phase 2A    │  │ Phase 2B    │  │ Phase 2C    │
   │ packages/   │  │ packages/   │  │ packages/   │
   │ mock        │  │ stream      │  │ rules       │
   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌──────▼──────┐        │
   │ Phase 3A    │  │ Phase 3B    │        │
   │ packages/   │  │ packages/   │        │
   │ insight     │  │ audit       │        │
   └──────┬──────┘  └──────┬──────┘        │
          │                │                │
          └────────────────┼────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Phase 4     │
                    │ Integration │
                    │ & Deploy    │
                    └─────────────┘
```

---

## Phase 0: Project Initialization (P0)

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| 0.1 | Create monorepo directory structure | ✅ Done |
| 0.2 | Create root pyproject.toml with uv workspace | ✅ Done |
| 0.3 | Create .env.example | ✅ Done |
| 0.4 | Create docker-compose.yml | ✅ Done |
| 0.5 | Create README.md | ✅ Done |
| 0.6 | Create pnpm-workspace.yaml | ✅ Done |

---

## Phase 1: libs/core - Shared Library (P0)

### Dependencies
- None (foundation for all modules)

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| 1.1 | Create data models (models/event.py, user.py) | ✅ Done |
| 1.2 | Create config management (config/settings.py) | ✅ Done |
| 1.3 | Create logging utils (utils/logging.py) | ✅ Done |
| 1.4 | Create datetime utils (utils/datetime.py) | ✅ Done |
| 1.5 | Create security module (security/auth.py, jwt.py) | ✅ Done |
| 1.6 | Create middleware (middleware/rate_limit.py, tracing.py) | ✅ Done |
| 1.7 | Create metrics module (metrics.py) | ✅ Done |
| 1.8 | Write unit tests | ✅ Done |

### Output Structure

```
libs/core/
├── pyproject.toml
└── src/behavior_core/
    ├── __init__.py
    ├── config/
    │   ├── __init__.py
    │   └── settings.py
    ├── models/
    │   ├── __init__.py
    │   ├── event.py
    │   └── user.py
    ├── security/
    │   ├── __init__.py
    │   ├── auth.py
    │   └── jwt.py
    ├── middleware/
    │   ├── __init__.py
    │   ├── rate_limit.py
    │   └── tracing.py
    ├── metrics.py
    └── utils/
        ├── __init__.py
        ├── logging.py
        └── datetime.py
```

---

## Phase 2A: packages/mock - Event Generator (P1)

### Dependencies
- libs/core

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| 2A.1 | Create behavior generator (generator.py) | ✅ Done |
| 2A.2 | Create Pulsar producer (producer.py) | ✅ Done |
| 2A.3 | Create scenario configs (scenarios.py) | ✅ Done |
| 2A.4 | Create FastAPI entry (main.py) | ✅ Done |
| 2A.5 | Write unit tests | ✅ Done |

---

## Phase 2B: packages/stream - Stream Processing (P1)

### Dependencies
- libs/core

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| 2B.1 | Create Faust app (app.py) | ✅ Done |
| 2B.2 | Create aggregation job (jobs/aggregation.py) | ✅ Done |
| 2B.3 | Create pattern detection (jobs/detection.py) | ✅ Done |
| 2B.4 | Create window operators (operators/window.py) | ✅ Done |
| 2B.5 | Create entry point (main.py) | ✅ Done |
| 2B.6 | Write unit tests | ✅ Done |

---

## Phase 2C: packages/rules - Rule Engine (P1)

### Dependencies
- libs/core

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| 2C.1 | Create rule models (models.py) | ✅ Done |
| 2C.2 | Create rule engine with AST parsing (engine.py) | ✅ Done |
| 2C.3 | Create rule loader (loader.py) | ✅ Done |
| 2C.4 | Create action handlers (actions/tagging.py, audit.py) | ✅ Done |
| 2C.5 | Create FastAPI entry (main.py) | ✅ Done |
| 2C.6 | Write unit tests | ✅ Done |

---

## Phase 3A: packages/insight - User Insight Service (P2)

### Dependencies
- libs/core
- packages/rules (action handling)

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| 3A.1 | Create tag service (services/tag_service.py) | ✅ Done |
| 3A.2 | Create user repository (repositories/user_repo.py) | ✅ Done |
| 3A.3 | Create tag API (routers/tags.py) | ✅ Done |
| 3A.4 | Create profile API (routers/profile.py) | ✅ Done |
| 3A.5 | Create FastAPI entry (main.py) | ✅ Done |
| 3A.6 | Write unit tests | ✅ Done |

---

## Phase 3B: packages/audit - Audit Service (P2)

### Dependencies
- libs/core
- packages/rules (trigger audit)

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| 3B.1 | Create audit service (services/audit_service.py) | ✅ Done |
| 3B.2 | Create audit repository (repositories/audit_repo.py) | ✅ Done |
| 3B.3 | Create audit API (routers/audit.py) | ✅ Done |
| 3B.4 | Create FastAPI entry (main.py) | ✅ Done |
| 3B.5 | Write unit tests | ✅ Done |

---

## Phase 4: Integration & Deployment (P3)

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| 4.1 | Create multi-service Dockerfile | ✅ Done |
| 4.2 | Update docker-compose.yml | ✅ Done |
| 4.3 | Create GitHub Actions CI | ✅ Done |
| 4.4 | Write integration tests | ✅ Done |
| 4.5 | Create documentation | ✅ Done |

---

## Development Commands

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/

# Run specific service
uv run uvicorn behavior_insight.main:app --port 8003

# Run stream processor
uv run python -m behavior_stream

# Build Docker image
docker build -f infrastructure/docker/Dockerfile --build-arg SERVICE=insight -t behaviorsense/insight:latest .
```

---

## Project Status

All phases completed. The project is ready for:
- Feature development
- Production deployment
- Frontend integration (apps/web)
