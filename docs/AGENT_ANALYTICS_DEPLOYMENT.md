# BehaviorSense Agent Analytics - Deployment Guide

## Quick Start (Docker Compose)

### Prerequisites
- Docker 20.10+
- Docker Compose v2.0+
- 4GB+ RAM recommended

### Start All Services

```bash
# Clone the repository
git clone https://github.com/afine907/behavior-sense.git
cd behavior-sense

# Start the full agent analytics stack
docker-compose -f infrastructure/docker/docker-compose.yml \
               -f infrastructure/docker/docker-compose.agent.yml up -d

# Check service health
docker-compose ps
```

### Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Agent Mock | http://localhost:8001 | Agent event generation |
| Rules Engine | http://localhost:8002 | Rule management |
| Agent Insight | http://localhost:8003 | Agent profiling |
| Audit Service | http://localhost:8004 | Audit workflow |
| Agent Logs | http://localhost:8005 | Event logs & traces |
| ClickHouse | http://localhost:8123 | Analytics DB |
| Redis | http://localhost:6379 | Cache & tags |
| PostgreSQL | http://localhost:5432 | Persistence |
| Pulsar | http://localhost:8080 | Message queue |

### Generate Test Data

```bash
# Generate normal agent events
curl -X POST http://localhost:8001/api/agent-mock/generate \
  -H "Content-Type: application/json" \
  -d '{"count": 100, "agent_type": "llm_agent"}'

# Start anomaly scenario
curl -X POST http://localhost:8001/api/agent-mock/scenario/start \
  -H "Content-Type: application/json" \
  -d '{"scenario": "loop", "params": {"loop_count": 20}}'
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Agent Mock │────▶│    Pulsar   │────▶│   Stream    │
│  (Port 8001)│     │  (Port 6650)│     │  Processor  │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────────────────┐
                    ▼                          ▼                  ▼
             ┌─────────────┐          ┌─────────────┐     ┌─────────────┐
             │  ClickHouse │          │    Rules    │     │   Alerts    │
             │  (Port 8123)│          │  (Port 8002)│     │    Topic    │
             └─────────────┘          └─────────────┘     └─────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────┐
                    ▼                          ▼                  ▼
             ┌─────────────┐          ┌─────────────┐     ┌─────────────┐
             │   Insight   │          │    Audit    │     │    Logs     │
             │  (Port 8003)│          │  (Port 8004)│     │  (Port 8005)│
             └─────────────┘          └─────────────┘     └─────────────┘
```

## Monitoring

### Prometheus Metrics

All services expose Prometheus metrics at `/metrics`:

```bash
curl http://localhost:8001/metrics
curl http://localhost:8002/metrics
curl http://localhost:8003/metrics
```

### Key Metrics

| Metric | Description |
|--------|-------------|
| `agent_events_total` | Total agent events processed |
| `agent_alerts_total` | Total alerts generated |
| `agent_cost_usd_total` | Total cost tracked |
| `agent_latency_ms` | Event processing latency |
| `rule_evaluations_total` | Rule evaluations performed |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PULSAR_URL` | `pulsar://localhost:6650` | Pulsar connection URL |
| `CLICKHOUSE_URL` | `http://localhost:8123` | ClickHouse HTTP URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL URL |
| `LOG_LEVEL` | `INFO` | Logging level |
| `RULES_DIR` | `./rules` | Rules YAML directory |

### Scaling

#### Horizontal Scaling
- Add more Stream consumers for higher throughput
- Add more FastAPI instances behind a load balancer
- Add Pulsar partitions for parallel processing

#### Vertical Scaling
- Increase ClickHouse memory for faster queries
- Increase Redis memory for larger tag storage
- Increase Pulsar memory for higher message throughput

## Troubleshooting

### Common Issues

**ClickHouse connection refused**
```bash
# Check ClickHouse health
docker-compose exec clickhouse clickhouse-client --query "SELECT 1"
```

**Pulsar not receiving messages**
```bash
# Check Pulsar topics
docker-compose exec pulsar bin/pulsar-admin topics list public/default
```

**High memory usage**
```bash
# Check service resource usage
docker stats
```
