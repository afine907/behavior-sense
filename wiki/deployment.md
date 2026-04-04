# Deployment Guide

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Production Deployment                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────┐                                                       │
│   │   Nginx     │                                                       │
│   │   Gateway   │                                                       │
│   └──────┬──────┘                                                       │
│          │                                                              │
│   ┌──────┴──────────────────────────────────────────────────┐          │
│   │                    FastAPI Services                      │          │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │          │
│   │  │  mock   │  │  rules  │  │ insight │  │  audit  │    │          │
│   │  │ :8001   │  │ :8002   │  │ :8003   │  │ :8004   │    │          │
│   │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │          │
│   └──────────────────────────────────────────────────────────┘          │
│                                      │                                   │
│   ┌──────────────────────────────────────────────────────────┐          │
│   │                    Stream Processing (Faust)              │          │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │          │
│   │  │ Worker-1 │  │ Worker-2 │  │ Worker-3 │  ...          │          │
│   │  └──────────┘  └──────────┘  └──────────┘               │          │
│   └──────────────────────────────────────────────────────────┘          │
│                                      │                                   │
│   ┌──────────────────────────────────────────────────────────┐          │
│   │                    Apache Pulsar Cluster                  │          │
│   │  ┌────────┐  ┌────────┐  ┌────────┐                      │          │
│   │  │Broker-1│  │Broker-2│  │Broker-3│                      │          │
│   │  └────────┘  └────────┘  └────────┘                      │          │
│   └──────────────────────────────────────────────────────────┘          │
│                                      │                                   │
│   ┌──────────────────────────────────────────────────────────┐          │
│   │                    Storage Layer                          │          │
│   │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐         │          │
│   │  │Postgres│  │ Redis  │  │   ES   │  │ClickHouse│        │          │
│   │  └────────┘  └────────┘  └────────┘  └────────┘         │          │
│   └──────────────────────────────────────────────────────────┘          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Environment Planning

### Development

| Component | Spec | Count |
|-----------|------|-------|
| Pulsar | 2C4G | 1 |
| PostgreSQL | 2C4G | 1 |
| Redis | 1C2G | 1 |
| ClickHouse | 2C4G | 1 |
| FastAPI Services | 1C2G | 1 each |
| Faust Worker | 1C2G | 1 |

### Production

| Component | Spec | Count |
|-----------|------|-------|
| Pulsar | 8C16G | 3 |
| PostgreSQL | 8C32G | 1 master + 2 replicas |
| Redis | 4C16G | 3 (cluster) |
| ClickHouse | 8C32G | 3 |
| FastAPI Services | 4C8G | 3 each |
| Faust Worker | 4C8G | 4 |

---

## Docker Deployment

### Multi-Service Dockerfile

```dockerfile
# infrastructure/docker/Dockerfile
# Build: docker build --build-arg SERVICE=insight -t behaviorsense/insight .

ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim AS builder
ARG SERVICE

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy workspace
COPY pyproject.toml uv.lock* ./
COPY libs/core libs/core
COPY packages/${SERVICE} packages/${SERVICE}

# Install dependencies
RUN uv sync --frozen --no-dev --package behavior-${SERVICE}

# Production stage
FROM python:${PYTHON_VERSION}-slim AS runtime
ARG SERVICE

WORKDIR /app

# Copy venv and source
COPY --from=builder /app/.venv /app/.venv
COPY libs/core/src libs/core/src
COPY packages/${SERVICE}/src packages/${SERVICE}/src

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/libs/core/src:/app/packages/${SERVICE}/src"

CMD ["uvicorn", "behavior_${SERVICE}.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build Commands

```bash
# Build specific service
docker build -f infrastructure/docker/Dockerfile --build-arg SERVICE=insight -t behaviorsense/insight:latest .

# Build all services
for svc in audit insight mock rules stream; do
  docker build -f infrastructure/docker/Dockerfile --build-arg SERVICE=$svc -t behaviorsense/$svc:latest .
done
```

---

## Docker Compose (Development)

```bash
# Start infrastructure
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f insight

# Stop
docker-compose down
```

---

## Kubernetes Deployment

### Deployment

```yaml
# k8s/insight-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: behavior-insight
  namespace: behavior-sense
spec:
  replicas: 3
  selector:
    matchLabels:
      app: behavior-insight
  template:
    spec:
      containers:
      - name: insight
        image: behaviorsense/insight:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
```

### HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: behavior-insight-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: behavior-insight
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Configuration

### Environment Variables

```bash
# .env.example

# Application
APP_NAME=behavior-sense
DEBUG=false
LOG_LEVEL=INFO

# Pulsar
PULSAR_URL=pulsar://localhost:6650

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=behavior_sense

# Redis
REDIS_URL=redis://localhost:6379

# ClickHouse
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9000

# Security
JWT_SECRET=change-me-in-production
```

---

## Monitoring

### Prometheus Config

```yaml
# infrastructure/docker/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'behavior-insight'
    static_configs:
      - targets: ['insight:8000']

  - job_name: 'behavior-audit'
    static_configs:
      - targets: ['audit:8000']
```

### Alert Rules

```yaml
groups:
  - name: behavior-sense
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: PulsarBacklog
        expr: pulsar_topic_backlog > 100000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Pulsar message backlog"
```

---

## Health Checks

```bash
# Check all services
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

---

## Release Checklist

- [ ] Unit tests pass (>80% coverage)
- [ ] Type checking passes (mypy)
- [ ] Linting passes (ruff)
- [ ] Integration tests pass
- [ ] Docker images build successfully
- [ ] Health checks pass
- [ ] Monitoring metrics normal
