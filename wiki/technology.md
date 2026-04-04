# Technology Stack

## Core Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Language | Python | 3.11+ | Runtime |
| Package Manager | [uv](https://docs.astral.sh/uv/) | 0.10+ | Dependency management |
| Web Framework | FastAPI | 0.109+ | REST API |
| Data Validation | Pydantic | 2.5+ | Models & serialization |
| Stream Processing | Faust | 0.11+ | Real-time processing |
| Message Queue | Apache Pulsar | 2.11+ | Event streaming |
| Database | PostgreSQL | 15+ | Persistent storage |
| Cache | Redis | 7+ | Caching & pub/sub |
| Analytics | ClickHouse | 23+ | OLAP queries |

---

## Why These Choices

### uv for Package Management

| Feature | uv | Poetry | pip |
|---------|-----|--------|-----|
| Speed | ⚡ 10-100x faster | Slow | Slow |
| Workspace | ✅ Native | Manual | ❌ |
| Lock file | ✅ uv.lock | ✅ poetry.lock | ❌ |
| Config | Standard pyproject.toml | Custom | requirements.txt |

```bash
# Install dependencies (fast!)
uv sync

# Add dependency
uv add httpx

# Run commands
uv run pytest
```

### FastAPI for Web Services

- **High Performance**: Based on Starlette, comparable to Node.js
- **Async Native**: Full asyncio support
- **Auto Documentation**: OpenAPI/Swagger generated automatically
- **Type Safety**: Pydantic models provide runtime validation

### Faust for Stream Processing

- **Pure Python**: No JVM required, easy deployment
- **Kafka/Pulsar Native**: Seamless integration
- **Stateful Processing**: RocksDB state store
- **Window Operations**: Time-based aggregations

---

## Project Structure

```
behavior-sense/
├── pyproject.toml           # Root config + uv workspace
├── uv.lock                   # Lock file
├── pnpm-workspace.yaml       # Frontend workspace (reserved)
│
├── libs/                     # Shared Python libraries
│   └── core/
│       ├── pyproject.toml
│       └── src/behavior_core/
│
├── packages/                 # Python microservices
│   ├── audit/
│   │   ├── pyproject.toml
│   │   └── src/behavior_audit/
│   ├── insight/
│   ├── mock/
│   ├── rules/
│   └── stream/
│
├── apps/                     # Frontend applications
│   └── web/                  # Next.js (reserved)
│
├── infrastructure/           # Infrastructure configs
│   └── docker/
│       ├── Dockerfile
│       ├── docker-compose.yml
│       └── prometheus.yml
│
├── tests/                    # Test suites
│   ├── conftest.py
│   ├── test_core/
│   ├── test_audit/
│   ├── test_insight/
│   ├── test_mock/
│   ├── test_rules/
│   └── test_stream/
│
└── wiki/                     # Documentation
```

---

## Development Setup

### Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Runtime |
| uv | 0.10+ | Package manager |
| Docker | 24+ | Container runtime |
| Docker Compose | 2.20+ | Local environment |

### Installation

```bash
# Clone repository
git clone https://github.com/afine907/behavior-sense.git
cd behavior-sense

# Install dependencies
uv sync

# Copy config
cp .env.example .env

# Start infrastructure
docker-compose up -d

# Run tests
uv run pytest
```

---

## Docker Configuration

### Multi-Service Dockerfile

```dockerfile
# Build with: docker build --build-arg SERVICE=insight .
ARG SERVICE
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY . .

# Install dependencies
RUN uv sync --frozen --no-dev --package behavior-${SERVICE}

# Run service
CMD ["uvicorn", "behavior_${SERVICE}.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  pulsar:
    image: apachepulsar/pulsar:2.11.2
    ports:
      - "6650:6650"
      - "8080:8080"

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: behavior_sense

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  clickhouse:
    image: clickhouse/clickhouse-server:23-alpine
    ports:
      - "8123:8123"
      - "9000:9000"
```

---

## Code Quality

### Linting & Formatting

```bash
# Lint code
uv run ruff check libs/ packages/

# Format code
uv run ruff format libs/ packages/

# Type check
uv run mypy libs/core/src packages/*/src
```

### Ruff Configuration

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4"]
```

---

## CI/CD

### GitHub Actions

```yaml
# .github/workflows/ci.yml
- name: Install uv
  uses: astral-sh/setup-uv@v3

- name: Install dependencies
  run: uv sync

- name: Run tests
  run: uv run pytest --cov
```

---

## Monitoring

### Prometheus Metrics

```python
# libs/core/src/behavior_core/metrics.py
from prometheus_client import Counter, Histogram

EVENTS_TOTAL = Counter(
    'behavior_events_total',
    'Total events processed',
    ['event_type']
)

PROCESSING_TIME = Histogram(
    'behavior_processing_seconds',
    'Event processing time'
)
```

### Health Check

```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "redis": await check_redis(),
        "postgres": await check_postgres(),
    }
```

---

## Testing

### Run Tests

```bash
# All tests
uv run pytest tests/

# With coverage
uv run pytest tests/ --cov=libs --cov=packages --cov-report=html

# Specific module
uv run pytest tests/test_core/
```

### Test Structure

```python
# tests/test_core/test_models.py
import pytest
from behavior_core.models.event import UserBehavior, EventType


def test_create_event():
    event = UserBehavior(
        user_id="user_001",
        event_type=EventType.VIEW,
    )
    assert event.user_id == "user_001"
    assert event.event_type == EventType.VIEW
```
