# BehaviorSense 微服务部署计划

## 目标

**定目标**：5个微服务 + 基础设施全部健康运行，API 可访问，数据流打通。

## 架构总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            BehaviorSense                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌────────┐│
│   │  Mock   │───▶│ Pulsar  │───▶│  Stream │───▶│  Rules  │───▶│ Insight││
│   │ :8001   │    │  :6650  │    │  Faust  │    │ :8002   │    │ :8003  ││
│   └─────────┘    └─────────┘    └─────────┘    └─────────┘    └────────┘│
│        │                                                        │        │
│        │              ┌─────────────────────────────────────────┘        │
│        │              ▼                                                  │
│        │       ┌─────────────┐                                          │
│        └──────▶│   Audit     │                                          │
│                │   :8004     │                                          │
│                └─────────────┘                                          │
│                                                                          │
│   基础设施：PostgreSQL:5432 | Redis:6379 | ClickHouse:8123 | ES:9200   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Phase 1: 基础设施启动

### 1.1 启动核心依赖

```bash
# 启动核心基础设施（PostgreSQL + Redis + Pulsar）
docker-compose up -d postgres redis pulsar

# 等待服务就绪（约 30-60 秒）
docker-compose logs -f pulsar  # 等待 Pulsar broker 启动完成
```

### 1.2 验证基础设施

```bash
# PostgreSQL
docker exec behavior-postgres pg_isready -U postgres

# Redis
docker exec behavior-redis redis-cli ping

# Pulsar
curl http://localhost:8080/admin/v2/persistent/public/default
```

### 1.3 初始化 Pulsar Topics

```bash
# 创建必要的 topics
docker exec behavior-pulsar bin/pulsar-admin topics create persistent://behavior-sense/default/user-behavior
docker exec behavior-pulsar bin/pulsar-admin topics create persistent://behavior-sense/default/aggregation-result
docker exec behavior-pulsar bin/pulsar-admin topics create persistent://behavior-sense/default/alerts
docker exec behavior-pulsar bin/pulsar-admin topics create persistent://behavior-sense/default/rule-match-result
```

### 1.4 初始化数据库

```bash
# 连接 PostgreSQL 创建表
docker exec -i behavior-postgres psql -U postgres -d behavior_sense << 'EOF'
-- 用户表
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(64) PRIMARY KEY,
    basic_info JSONB DEFAULT '{}',
    behavior_tags JSONB DEFAULT '[]',
    stat_tags JSONB DEFAULT '{}',
    predict_tags JSONB DEFAULT '{}',
    risk_level VARCHAR(32) DEFAULT 'low',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户统计表
CREATE TABLE IF NOT EXISTS user_stats (
    user_id VARCHAR(64) PRIMARY KEY,
    total_events INTEGER DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    total_purchases INTEGER DEFAULT 0,
    total_amount FLOAT DEFAULT 0.0,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 审核工单表
CREATE TABLE IF NOT EXISTS audit_orders (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    rule_id VARCHAR(64) NOT NULL,
    trigger_data JSONB DEFAULT '{}',
    audit_level VARCHAR(32) DEFAULT 'MEDIUM',
    status VARCHAR(32) DEFAULT 'pending',
    assignee VARCHAR(64),
    reviewer_note TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_orders_user ON audit_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_orders_status ON audit_orders(status);
CREATE INDEX IF NOT EXISTS idx_audit_orders_assignee ON audit_orders(assignee);
EOF
```

## Phase 2: 微服务启动

### 2.1 服务启动顺序

按依赖关系启动，确保上下游就绪：

```
1. Mock (无外部依赖) ──────────────────────────────► 可独立启动
2. Rules (无外部依赖) ─────────────────────────────► 可独立启动  
3. Insight (依赖 Redis + PostgreSQL) ─────────────► 基础设施就绪后启动
4. Audit (依赖 Redis + PostgreSQL) ───────────────► 基础设施就绪后启动
5. Stream (依赖 Pulsar) ─────────────────────────► Pulsar 就绪后启动
```

### 2.2 启动命令

```bash
# 终端 1: Mock 服务
cd d:/Code/behavior-sense
uv run uvicorn behavior_mock.main:app --host 0.0.0.0 --port 8001 --reload

# 终端 2: Rules 服务
uv run uvicorn behavior_rules.main:app --host 0.0.0.0 --port 8002 --reload

# 终端 3: Insight 服务
uv run uvicorn behavior_insight.main:app --host 0.0.0.0 --port 8003 --reload

# 终端 4: Audit 服务
uv run uvicorn behavior_audit.main:app --host 0.0.0.0 --port 8004 --reload

# 终端 5: Stream 服务（Faust）
uv run python -m behavior_stream
```

### 2.3 健康检查

```bash
# 检查所有服务健康状态
curl http://localhost:8001/health  # Mock
curl http://localhost:8002/health  # Rules
curl http://localhost:8003/health  # Insight
curl http://localhost:8004/health  # Audit
```

## Phase 3: API 验证

### 3.1 Mock 服务验证

```bash
# 生成测试事件
curl -X POST http://localhost:8001/api/mock/generate \
  -H "Content-Type: application/json" \
  -d '{"count": 10, "user_pool_size": 5}'

# 启动场景
curl -X POST http://localhost:8001/api/mock/scenario/start \
  -H "Content-Type: application/json" \
  -d '{"scenario_type": "normal", "duration_seconds": 30, "rate_per_second": 5}'
```

### 3.2 Rules 服务验证

```bash
# 创建规则
curl -X POST http://localhost:8002/api/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "高价值用户",
    "condition": "purchase_count >= 5",
    "actions": [{"type": "TAG_USER", "params": {"tags": ["high_value"]}}],
    "enabled": true
  }'

# 评估规则
curl -X POST http://localhost:8002/api/rules/evaluate \
  -H "Content-Type: application/json" \
  -d '{"context": {"user_id": "user_001", "purchase_count": 10}}'
```

### 3.3 Insight 服务验证

```bash
# 更新用户标签
curl -X PUT http://localhost:8003/api/insight/user/user_001/tag \
  -H "Content-Type: application/json" \
  -d '{"tag_name": "level", "tag_value": "vip", "source": "MANUAL"}'

# 获取用户标签
curl http://localhost:8003/api/insight/user/user_001/tags

# 更新用户画像
curl -X PUT http://localhost:8003/api/insight/user/user_001/profile \
  -H "Content-Type: application/json" \
  -d '{"basic_info": {"name": "Test"}, "risk_level": "low"}'
```

### 3.4 Audit 服务验证

```bash
# 创建审核工单
curl -X POST http://localhost:8004/api/audit/order \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "rule_id": "rule_001",
    "trigger_data": {"event": "suspicious_login"},
    "audit_level": "HIGH"
  }'

# 获取待办列表
curl http://localhost:8004/api/audit/orders?status=pending

# 分配审核人
curl -X PUT http://localhost:8004/api/audit/order/{order_id}/assign \
  -H "Content-Type: application/json" \
  -d '{"assignee": "reviewer_001"}'
```

## Phase 4: 数据流验证

### 4.1 端到端流程验证

```bash
# 1. Mock 生成事件
curl -X POST http://localhost:8001/api/mock/generate \
  -H "Content-Type: application/json" \
  -d '{"count": 100, "user_pool_size": 10}'

# 2. Rules 评估（dry-run）
curl -X POST http://localhost:8002/api/rules/evaluate/dry-run \
  -H "Content-Type: application/json" \
  -d '{"context": {"user_id": "test_user", "purchase_count": 10, "total_amount": 5000}}'

# 3. Insight 查询结果
curl http://localhost:8003/api/insight/user/test_user/tags
```

### 4.2 Stream 服务验证

```bash
# 检查 Faust 应用状态
curl http://localhost:6066/stats  # Faust 默认监控端口
```

## Phase 5: 故障排查

### 常见问题

| 问题 | 症状 | 解决方案 |
|------|------|----------|
| Pulsar 启动慢 | 连接超时 | 等待 60s 或检查日志 `docker-compose logs pulsar` |
| PostgreSQL 连接失败 | `connection refused` | 检查容器状态 `docker ps` |
| Redis 连接失败 | `ConnectionError` | 确认 Redis 端口映射正确 |
| Insight/Audit 健康检查 degraded | `redis: error` | 检查 Redis 连接配置 |

### 日志查看

```bash
# 查看服务日志
docker-compose logs -f pulsar
docker-compose logs -f postgres
docker-compose logs -f redis

# 查看应用日志（在启动终端查看）
```

## 快速启动脚本

```bash
#!/bin/bash
# quick-start.sh - 一键启动所有服务

set -e

echo "=== Phase 1: 启动基础设施 ==="
docker-compose up -d postgres redis pulsar

echo "等待基础设施就绪..."
sleep 30

echo "=== Phase 2: 初始化 Pulsar Topics ==="
docker exec behavior-pulsar bin/pulsar-admin topics create persistent://behavior-sense/default/user-behavior 2>/dev/null || true
docker exec behavior-pulsar bin/pulsar-admin topics create persistent://behavior-sense/default/aggregation-result 2>/dev/null || true

echo "=== Phase 3: 启动微服务 ==="
echo "请在不同终端运行以下命令："
echo "  终端1: uv run uvicorn behavior_mock.main:app --port 8001 --reload"
echo "  终端2: uv run uvicorn behavior_rules.main:app --port 8002 --reload"
echo "  终端3: uv run uvicorn behavior_insight.main:app --port 8003 --reload"
echo "  终端4: uv run uvicorn behavior_audit.main:app --port 8004 --reload"
echo "  终端5: uv run python -m behavior_stream"

echo "=== 验证服务 ==="
sleep 5
curl -s http://localhost:8001/health | jq .
curl -s http://localhost:8002/health | jq .
curl -s http://localhost:8003/health | jq .
curl -s http://localhost:8004/health | jq .

echo "=== 所有服务已启动 ==="
```

## 服务依赖矩阵

| 服务 | PostgreSQL | Redis | Pulsar | 端口 |
|------|:----------:|:-----:|:------:|------|
| Mock | ❌ | ❌ | ✉️ | 8001 |
| Rules | ❌ | ❌ | ❌ | 8002 |
| Insight | ✅ | ✅ | ❌ | 8003 |
| Audit | ✅ | ✅ | ❌ | 8004 |
| Stream | ❌ | ❌ | ✅ | - |

## 验收标准

- [ ] PostgreSQL: `pg_isready` 返回 OK
- [ ] Redis: `ping` 返回 PONG
- [ ] Pulsar: admin API 返回 200
- [ ] Mock: `/health` 返回 200
- [ ] Rules: `/health` 返回 200
- [ ] Insight: `/health` 返回 200 (redis: ok, database: ok)
- [ ] Audit: `/health` 返回 200
- [ ] API 文档可访问: `/docs`
