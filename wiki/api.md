# API 设计

## API 概览

所有 API 遵循 RESTful 风格，统一返回格式。

### 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "traceId": "abc123"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| code | int | 0 成功，非 0 失败 |
| message | string | 消息 |
| data | object | 响应数据 |
| traceId | string | 请求追踪ID |

### 错误码定义

| 错误码 | 描述 |
|--------|------|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | 资源不存在 |
| 1003 | 权限不足 |
| 2001 | 服务内部错误 |
| 2002 | 外部服务调用失败 |
| 3001 | 限流中 |
| 3002 | 熔断中 |

---

## 用户行为 API

### 生成用户行为

**POST** `/api/mock/generate`

```json
// Request
{
  "count": 100,
  "eventTypes": ["VIEW", "CLICK", "PURCHASE"],
  "userCount": 50
}

// Response
{
  "code": 0,
  "message": "success",
  "data": {
    "generatedCount": 100,
    "durationMs": 150
  }
}
```

### 启动场景模拟

**POST** `/api/mock/scenario/start`

```json
// Request
{
  "scenario": "flash_sale",
  "durationSeconds": 3600,
  "usersPerSecond": 100
}

// Response
{
  "code": 0,
  "message": "success",
  "data": {
    "scenarioId": "scenario_001"
  }
}
```

### 停止场景模拟

**POST** `/api/mock/scenario/{scenarioId}/stop`

```json
// Response
{
  "code": 0,
  "message": "success",
  "data": {
    "totalGenerated": 360000
  }
}
```

---

## 规则管理 API

### 创建规则

**POST** `/api/rules`

```json
// Request
{
  "name": "高风险用户检测",
  "condition": "login_fail_count > 5 AND last_30min",
  "priority": 1,
  "enabled": true,
  "actions": [
    {
      "type": "TAG_USER",
      "params": {
        "tags": ["high_risk"]
      }
    },
    {
      "type": "TRIGGER_AUDIT",
      "params": {
        "level": "HIGH"
      }
    }
  ]
}

// Response
{
  "code": 0,
  "message": "success",
  "data": {
    "ruleId": "rule_001"
  }
}
```

### 更新规则

**PUT** `/api/rules/{ruleId}`

```json
// Request
{
  "name": "高风险用户检测",
  "condition": "login_fail_count > 3 AND last_30min",
  "priority": 1,
  "enabled": true,
  "actions": [...]
}

// Response
{
  "code": 0,
  "message": "success",
  "data": null
}
```

### 查询规则

**GET** `/api/rules/{ruleId}`

```json
// Response
{
  "code": 0,
  "message": "success",
  "data": {
    "ruleId": "rule_001",
    "name": "高风险用户检测",
    "condition": "login_fail_count > 3 AND last_30min",
    "priority": 1,
    "enabled": true,
    "actions": [...],
    "createTime": "2024-01-01T00:00:00Z",
    "updateTime": "2024-01-02T00:00:00Z"
  }
}
```

### 规则列表

**GET** `/api/rules`

```json
// Request
?page=1&size=20&enabled=true

// Response
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "size": 20,
    "list": [
      {
        "ruleId": "rule_001",
        "name": "...",
        "priority": 1,
        "enabled": true
      }
    ]
  }
}
```

### 删除规则

**DELETE** `/api/rules/{ruleId}`

---

## 标签管理 API

### 查询用户标签

**GET** `/api/insight/user/{userId}/tags`

```json
// Response
{
  "code": 0,
  "message": "success",
  "data": {
    "userId": "user_001",
    "tags": {
      "level": {"value": "VIP", "updateTime": "2024-01-01T00:00:00Z"},
      "activity": {"value": "HIGH", "updateTime": "2024-01-01T00:00:00Z"}
    },
    "lastUpdateTime": "2024-01-01T00:00:00Z"
  }
}
```

### 查询用户画像

**GET** `/api/insight/user/{userId}/profile`

```json
// Response
{
  "code": 0,
  "message": "success",
  "data": {
    "userId": "user_001",
    "basicInfo": {
      "registerTime": "2023-01-01T00:00:00Z",
      "region": "北京"
    },
    "behaviorTags": [...],
    "statTags": [...],
    "riskProfile": {...},
    "preferenceProfile": {...}
  }
}
```

### 批量查询标签

**POST** `/api/insight/user/tags/batch`

```json
// Request
{
  "userIds": ["user_001", "user_002", "user_003"],
  "tagNames": ["level", "activity"]
}

// Response
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "userId": "user_001",
      "tags": {...}
    }
  ]
}
```

### 手动更新标签

**PUT** `/api/insight/user/{userId}/tag`

```json
// Request
{
  "tagName": "level",
  "tagValue": "VIP",
  "source": "manual",
  "operator": "admin"
}

// Response
{
  "code": 0,
  "message": "success",
  "data": null
}
```

### 标签统计

**GET** `/api/insight/tags/statistics`

```json
// Request
?tagName=level

// Response
{
  "code": 0,
  "message": "success",
  "data": {
    "tagName": "level",
    "total": 10000,
    "distribution": {
      "VIP": 1000,
      "NORMAL": 8000,
      "NEW": 1000
    }
  }
}
```

---

## 审核管理 API

### 创建审核工单

**POST** `/api/audit/order`

```json
// Request
{
  "userId": "user_001",
  "ruleId": "rule_001",
  "triggerData": {...},
  "auditLevel": "HIGH"
}

// Response
{
  "code": 0,
  "message": "success",
  "data": {
    "orderId": "audit_001"
  }
}
```

### 查询审核工单

**GET** `/api/audit/order/{orderId}`

```json
// Response
{
  "code": 0,
  "message": "success",
  "data": {
    "orderId": "audit_001",
    "userId": "user_001",
    "ruleId": "rule_001",
    "triggerData": {...},
    "auditLevel": "HIGH",
    "status": "PENDING",
    "assignee": null,
    "createTime": "2024-01-01T00:00:00Z",
    "updateTime": "2024-01-01T00:00:00Z"
  }
}
```

### 提交审核结果

**PUT** `/api/audit/order/{orderId}/review`

```json
// Request
{
  "status": "APPROVED",
  "reviewerNote": "经核实为正常行为"
}

// Response
{
  "code": 0,
  "message": "success",
  "data": null
}
```

### 审核列表查询

**GET** `/api/audit/orders`

```json
// Request
?page=1&size=20&status=PENDING&assignee=admin

// Response
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "size": 20,
    "list": [...]
  }
}
```

### 我的待办审核

**GET** `/api/audit/orders/todo`

```json
// Request
?page=1&size=20

// Response
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 10,
    "list": [...]
  }
}
```

---

## 监控指标 API

### 获取系统指标

**GET** `/api/monitor/metrics`

```json
// Request
?metrics=qps,latency,error_rate

// Response
{
  "code": 0,
  "message": "success",
  "data": {
    "qps": {
      "current": 1000,
      "avg_1m": 950,
      "avg_5m": 900
    },
    "latency": {
      "p50": 10,
      "p90": 50,
      "p99": 100
    },
    "error_rate": {
      "current": 0.001,
      "avg_1m": 0.002
    }
  }
}
```

### 获取流处理状态

**GET** `/api/monitor/flink/status`

```json
// Response
{
  "code": 0,
  "message": "success",
  "data": {
    "jobId": "job_001",
    "status": "RUNNING",
    "lastCheckpoint": "2024-01-01T00:00:00Z",
    "processedRecords": 1000000,
    "pendingRecords": 100
  }
}
```

---

## WebSocket 实时推送

### 连接地址

```
ws://host:port/api/ws/realtime
```

### 订阅主题

```json
// 订阅
{
  "type": "SUBSCRIBE",
  "topic": "audit_order"
}

// 响应
{
  "type": "ACK",
  "topic": "audit_order"
}
```

### 推送消息格式

```json
{
  "type": "MESSAGE",
  "topic": "audit_order",
  "data": {
    "orderId": "audit_001",
    "status": "PENDING"
  }
}
```

---

## 认证与授权

### 认证方式

采用 JWT Token 认证：

```
Authorization: Bearer <token>
```

### Token 格式

```json
{
  "sub": "user_001",
  "username": "admin",
  "roles": ["ADMIN", "AUDITOR"],
  "exp": 1704067200
}
```

### 接口权限

| 接口 | 角色要求 |
|------|----------|
| /api/mock/* | ADMIN |
| /api/rules/* | ADMIN |
| /api/insight/user/* | ADMIN, ANALYST |
| /api/audit/order/* | ADMIN, AUDITOR |
| /api/monitor/* | ADMIN, MONITOR |