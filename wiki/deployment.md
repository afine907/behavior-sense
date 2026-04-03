# 部署方案

## 部署架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           生产环境部署架构                                │
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
│   │  │(多实例) │  │(多实例) │  │(多实例) │  │(多实例) │    │          │
│   │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │          │
│   └──────────────────────────────────────────────────────────┘          │
│                                      │                                   │
│   ┌──────────────────────────────────────────────────────────┐          │
│   │                    Stream Processing                      │          │
│   │  ┌────────────────────────────────────────────────────┐  │          │
│   │  │              Faust / PyFlink Workers               │  │          │
│   │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │  │          │
│   │  │  │ Worker-1 │  │ Worker-2 │  │ Worker-3 │  ...    │  │          │
│   │  │  └──────────┘  └──────────┘  └──────────┘         │  │          │
│   │  └────────────────────────────────────────────────────┘  │          │
│   └──────────────────────────────────────────────────────────┘          │
│                                      │                                   │
│   ┌──────────────────────────────────────────────────────────┐          │
│   │                    Message Queue                          │          │
│   │  ┌────────────────────────────────────────────────────┐  │          │
│   │  │                 Apache Pulsar                      │  │          │
│   │  │  ┌────────┐  ┌────────┐  ┌────────┐               │  │          │
│   │  │  │Broker-1│  │Broker-2│  │Broker-3│               │  │          │
│   │  │  └────────┘  └────────┘  └────────┘               │  │          │
│   │  └────────────────────────────────────────────────────┘  │          │
│   └──────────────────────────────────────────────────────────┘          │
│                                      │                                   │
│   ┌──────────────────────────────────────────────────────────┐          │
│   │                    Storage Layer                          │          │
│   │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐         │          │
│   │  │Postgres│  │ Redis  │  │   ES   │  │ClickHouse│        │          │
│   │  │(主从)  │  │(集群)  │  │(集群)  │  │ (集群)  │         │          │
│   │  └────────┘  └────────┘  └────────┘  └────────┘         │          │
│   └──────────────────────────────────────────────────────────┘          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 环境规划

### 开发环境

| 组件 | 规格 | 数量 |
|------|------|------|
| Pulsar | 2C4G | 1 |
| PostgreSQL | 2C4G | 1 |
| Redis | 1C2G | 1 |
| ClickHouse | 2C4G | 1 |
| FastAPI 服务 | 1C2G | 各 1 实例 |
| Faust Worker | 1C2G | 1 |

### 测试环境

| 组件 | 规格 | 数量 |
|------|------|------|
| Pulsar | 4C8G | 3 |
| PostgreSQL | 4C8G | 1 主 1 从 |
| Redis | 2C4G | 1 |
| ClickHouse | 4C8G | 2 |
| FastAPI 服务 | 2C4G | 各 2 实例 |
| Faust Worker | 2C4G | 2 |

### 生产环境

| 组件 | 规格 | 数量 |
|------|------|------|
| Pulsar | 8C16G | 3 |
| PostgreSQL | 8C32G | 1 主 2 从 |
| Redis | 4C16G | 3 |
| ClickHouse | 8C32G | 3 |
| FastAPI 服务 | 4C8G | 各 3 实例 |
| Faust Worker | 4C8G | 4 |

---

## Docker 部署

### Dockerfile

```dockerfile
# docker/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY pyproject.toml .
RUN pip install --no-cache-dir -e "."

# 复制代码
COPY . .

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 默认命令
CMD ["uvicorn", "behavior_insight.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (开发环境)

```yaml
# docker-compose.yml
version: '3.8'

services:
  # ===== 基础设施 =====
  pulsar:
    image: apachepulsar/pulsar:2.11.2
    container_name: behavior-pulsar
    ports:
      - "6650:6650"
      - "8080:8080"
    environment:
      - PULSAR_PREFIX_clusterName=behavior-sense
    networks:
      - behavior-net

  postgres:
    image: postgres:15-alpine
    container_name: behavior-postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=behavior_sense
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - behavior-net

  redis:
    image: redis:7-alpine
    container_name: behavior-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - behavior-net

  clickhouse:
    image: clickhouse/clickhouse-server:23-alpine
    container_name: behavior-clickhouse
    ports:
      - "8123:8123"
      - "9000:9000"
    volumes:
      - clickhouse-data:/var/lib/clickhouse
    networks:
      - behavior-net

  elasticsearch:
    image: elasticsearch:8.11.0
    container_name: behavior-es
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms2g -Xmx2g
    volumes:
      - es-data:/usr/share/elasticsearch/data
    networks:
      - behavior-net

  # ===== 应用服务 =====
  mock:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: behavior-mock
    ports:
      - "8001:8000"
    command: uvicorn behavior_mock.main:app --host 0.0.0.0 --port 8000
    environment:
      - PULSAR_URL=pulsar://pulsar:6650
    depends_on:
      - pulsar
    networks:
      - behavior-net

  insight:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: behavior-insight
    ports:
      - "8003:8000"
    command: uvicorn behavior_insight.main:app --host 0.0.0.0 --port 8000
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres/behavior_sense
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    networks:
      - behavior-net

  rules:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: behavior-rules
    ports:
      - "8002:8000"
    command: uvicorn behavior_rules.main:app --host 0.0.0.0 --port 8000
    environment:
      - PULSAR_URL=pulsar://pulsar:6650
      - REDIS_URL=redis://redis:6379
    depends_on:
      - pulsar
      - redis
    networks:
      - behavior-net

  audit:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: behavior-audit
    ports:
      - "8004:8000"
    command: uvicorn behavior_audit.main:app --host 0.0.0.0 --port 8000
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres/behavior_sense
    depends_on:
      - postgres
    networks:
      - behavior-net

  # ===== 流处理 =====
  stream-worker:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: behavior-stream
    command: python -m behavior_stream
    environment:
      - PULSAR_URL=pulsar://pulsar:6650
      - REDIS_URL=redis://redis:6379
    depends_on:
      - pulsar
      - redis
    networks:
      - behavior-net

  # ===== 监控 =====
  prometheus:
    image: prom/prometheus:latest
    container_name: behavior-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - behavior-net

  grafana:
    image: grafana/grafana:latest
    container_name: behavior-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - behavior-net

volumes:
  postgres-data:
  redis-data:
  clickhouse-data:
  es-data:
  prometheus-data:
  grafana-data:

networks:
  behavior-net:
    driver: bridge
```

### 启动命令

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f insight

# 停止所有服务
docker-compose down

# 重新构建
docker-compose up -d --build
```

---

## Kubernetes 部署

### Deployment 配置

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
    metadata:
      labels:
        app: behavior-insight
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
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: behavior-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: behavior-secrets
              key: redis-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service 配置

```yaml
# k8s/insight-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: behavior-insight
  namespace: behavior-sense
spec:
  selector:
    app: behavior-insight
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: behavior-config
  namespace: behavior-sense
data:
  PULSAR_URL: "pulsar://pulsar:6650"
  PULSAR_TENANT: "behavior-sense"
  PULSAR_NAMESPACE: "default"
  LOG_LEVEL: "INFO"
```

### HPA 自动扩缩

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: behavior-insight-hpa
  namespace: behavior-sense
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
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 配置管理

### 环境变量

```bash
# .env.example

# 应用配置
APP_NAME=behavior-sense
DEBUG=false
LOG_LEVEL=INFO

# Pulsar
PULSAR_URL=pulsar://localhost:6650
PULSAR_TENANT=behavior-sense
PULSAR_NAMESPACE=default

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
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=

# Elasticsearch
ES_HOST=localhost
ES_PORT=9200
```

### Pydantic Settings

```python
# behavior_core/config/settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    app_name: str = "behavior-sense"
    debug: bool = False
    log_level: str = "INFO"

    # Pulsar
    pulsar_url: str = "pulsar://localhost:6650"
    pulsar_tenant: str = "behavior-sense"
    pulsar_namespace: str = "default"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "behavior_sense"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # ClickHouse
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 9000

    class Config:
        env_file = ".env"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## 监控配置

### Prometheus 配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'behavior-mock'
    static_configs:
      - targets: ['mock:8000']

  - job_name: 'behavior-rules'
    static_configs:
      - targets: ['rules:8000']

  - job_name: 'behavior-insight'
    static_configs:
      - targets: ['insight:8000']

  - job_name: 'behavior-audit'
    static_configs:
      - targets: ['audit:8000']
```

### 告警规则

```yaml
# alerts.yml
groups:
  - name: behavior-sense
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "高错误率"

      - alert: PulsarBacklog
        expr: pulsar_topic_backlog > 100000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Pulsar 消息积压"

      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "请求延迟过高"
```

---

## CI/CD 配置

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -e ".[dev]"

    - name: Run linting
      run: |
        ruff check .

    - name: Run type checking
      run: |
        mypy behavior_core behavior_mock behavior_insight

    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml
      env:
        DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost/behavior_sense
        REDIS_URL: redis://localhost:6379

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Build Docker image
      run: |
        docker build -t behaviorsense/insight:${{ github.sha }} .
        docker push behaviorsense/insight:${{ github.sha }}
```

---

## 日志管理

### 结构化日志

```python
# behavior_core/utils/logging.py
import structlog
import logging

def setup_logging():
    """配置结构化日志"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(format="%(message)s")
```

### 日志收集

```yaml
# fluentd.conf
<source>
  @type forward
  port 24224
</source>

<match behavior.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  logstash_format true
  logstash_prefix behavior-logs
</match>
```

---

## 发布流程

### 发布检查清单

- [ ] 单元测试通过 (>80% 覆盖率)
- [ ] 类型检查通过 (mypy)
- [ ] 代码规范检查 (ruff)
- [ ] 集成测试通过
- [ ] Docker 镜像构建成功
- [ ] 灰度发布验证
- [ ] 监控指标正常

### 滚动发布

```bash
# Kubernetes 滚动更新
kubectl rollout status deployment/behavior-insight -n behavior-sense

# 查看发布状态
kubectl rollout status deployment/behavior-insight -n behavior-sense

# 回滚
kubectl rollout undo deployment/behavior-insight -n behavior-sense
```

### 健康检查

```bash
# 检查服务健康
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```