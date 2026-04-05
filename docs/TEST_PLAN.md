# BehaviorSense 端到端测试计划

> **目标**: 达到上线标准，确保前后端整条链路稳定可靠
> **创建日期**: 2026-04-05
> **负责人**: Claude Code Agent

---

## 1. 项目架构概览

### 1.1 后端服务

| 服务 | 端口 | 职责 | 依赖 |
|------|------|------|------|
| Mock | 8001 | 事件生成器 | Pulsar |
| Rules | 8002 | 规则引擎 | - |
| Insight | 8003 | 用户洞察/标签 | PostgreSQL, Redis, ClickHouse |
| Audit | 8004 | 人工审核工作流 | PostgreSQL, Redis |
| Stream | - | 实时流处理 | Pulsar, Redis |

### 1.2 前端应用

| 页面 | 路由 | 功能 | 调用服务 |
|------|------|------|----------|
| Dashboard | `/` | 总览仪表盘 | 所有服务健康检查 |
| Mock | `/mock` | 事件生成/场景管理 | Mock API |
| Rules | `/rules` | 规则 CRUD/评估 | Rules API |
| Insight | `/insight` | 用户画像/标签管理 | Insight API |
| Audit | `/audit` | 审核工单管理 | Audit API |
| Monitor | `/monitor` | 系统监控 | Prometheus |

### 1.3 基础设施

| 组件 | 端口 | 用途 |
|------|------|------|
| PostgreSQL | 5432 | 持久化存储 |
| Redis | 6379 | 缓存/Pub-Sub |
| Pulsar | 6650/8080 | 消息队列 |
| ClickHouse | 8123/9000 | OLAP 分析 |
| Elasticsearch | 9200 | 日志搜索 |
| Prometheus | 9090 | 指标采集 |
| Grafana | 3000 | 可视化监控 |

---

## 2. 测试策略矩阵

### 2.1 测试金字塔

```
                    ┌─────────────────┐
                    │    E2E Test     │  少量，关键用户场景
                    │    (Playwright) │  
                    ├─────────────────┤
                    │  Integration    │  中等，服务间交互
                    │    (pytest)     │
                    ├─────────────────┤
                    │   Unit Test     │  大量，函数/组件级别
                    │ (pytest/Jest)   │
                    └─────────────────┘
```

### 2.2 覆盖率目标

| 层级 | 当前 | 目标 | 优先级 |
|------|------|------|--------|
| 后端单元测试 | ~60% | 80% | P0 |
| 后端集成测试 | ~40% | 70% | P0 |
| 前端单元测试 | 0% | 60% | P1 |
| 前端E2E测试 | 0% | 关键路径100% | P0 |
| 端到端场景 | 0% | 10个核心场景 | P0 |

---

## 3. Phase 1: 基础设施层验证

### 3.1 数据库 (PostgreSQL)

```bash
# 测试项
□ 连接池健康检查
□ 事务隔离级别验证
□ 索引效率分析
□ 数据库迁移脚本验证
□ 备份/恢复流程测试
□ 连接断开重连机制
□ 慢查询分析 (< 100ms)
```

### 3.2 缓存 (Redis)

```bash
# 测试项
□ 连接池验证
□ 读写延迟 (< 1ms)
□ 过期策略验证
□ 持久化配置 (AOF/RDB)
□ 主从同步 (如适用)
□ 内存使用监控
□ 热点 Key 分析
```

### 3.3 消息队列 (Pulsar)

```bash
# 测试项
□ 生产者连接验证
□ 消费者订阅验证
□ 消息持久化
□ 消息重试机制
□ 死信队列处理
□ 消息顺序保证
□ 背压处理
□ 消费者组再平衡
```

### 3.4 分析存储 (ClickHouse)

```bash
# 测试项
□ 连接验证
□ 写入性能测试
□ 查询性能测试 (< 1s for 1M rows)
□ 数据分区策略
□ TTL 配置验证
```

---

## 4. Phase 2: 后端服务测试

### 4.1 Mock 服务 (端口 8001)

#### 单元测试
```python
# tests/test_api/test_mock_api.py
□ test_generate_events_default
□ test_generate_events_with_event_types
□ test_generate_events_weighted
□ test_generate_events_invalid_type
□ test_generate_events_count_limit
□ test_start_normal_scenario
□ test_start_flash_sale_scenario
□ test_start_abnormal_scenario
□ test_scenario_pause_resume
□ test_scenario_stop_delete
□ test_scenario_duplicate_id
```

#### 集成测试
```python
□ test_pulsar_producer_connection
□ test_event_send_to_pulsar
□ test_scenario_persistence
□ test_rate_limiting
□ test_concurrent_scenario_creation
```

### 4.2 Rules 服务 (端口 8002)

#### 单元测试
```python
# tests/test_api/test_rules_api.py
□ test_create_rule
□ test_update_rule
□ test_delete_rule
□ test_get_rule
□ test_list_rules_pagination
□ test_evaluate_rules
□ test_dry_run_evaluate
□ test_validate_rule_condition
□ test_rule_priority_sorting
□ test_rule_tag_filtering
```

#### 集成测试
```python
□ test_rule_engine_evaluation
□ test_action_handler_tag_user
□ test_action_handler_trigger_audit
□ test_yaml_rule_loading
□ test_rule_hot_reload
□ test_complex_condition_parsing
```

### 4.3 Insight 服务 (端口 8003)

#### 单元测试
```python
# tests/test_api/test_insight_api.py
□ test_update_user_tag
□ test_get_user_tags
□ test_delete_user_tag
□ test_batch_get_tags
□ test_get_users_by_tag
□ test_get_user_profile
□ test_update_user_profile
□ test_get_users_by_risk
□ test_delete_user
□ test_tag_statistics
```

#### 集成测试
```python
□ test_redis_tag_persistence
□ test_postgres_user_profile
□ test_clickhouse_analytics
□ test_tag_expiration
□ test_concurrent_tag_updates
```

### 4.4 Audit 服务 (端口 8004)

#### 单元测试
```python
# tests/test_api/test_audit_api.py
□ test_create_order
□ test_get_order
□ test_assign_order
□ test_submit_review_approve
□ test_submit_review_reject
□ test_reopen_order
□ test_list_orders_pagination
□ test_list_orders_filter_status
□ test_batch_assign
□ test_order_stats
```

#### 集成测试
```python
□ test_audit_workflow_complete
□ test_order_assignment_notification
□ test_order_escalation
□ test_audit_metrics
□ test_concurrent_review
```

### 4.5 Stream 服务

#### 单元测试
```python
□ test_event_parsing
□ test_window_aggregation
□ test_pattern_detection_login_failure
□ test_pattern_detection_high_frequency
□ test_pattern_detection_rapid_click
□ test_pattern_detection_unusual_purchase
□ test_state_cleanup
```

#### 集成测试
```python
□ test_pulsar_consumer_connection
□ test_pulsar_producer_connection
□ test_end_to_end_event_flow
□ test_alert_generation
□ test_aggregation_output
```

---

## 5. Phase 3: 前端应用测试

### 5.1 组件单元测试 (Jest + React Testing Library)

```typescript
// apps/web/src/components/__tests__/

// Dashboard 组件
□ metric-card.test.tsx
□ trend-chart.test.tsx
□ service-status.test.tsx
□ pending-audits-list.test.tsx

// Rules 组件
□ rule-card.test.tsx
□ condition-builder.test.tsx
□ action-editor.test.tsx
□ rule-form.test.tsx

// Insight 组件
□ user-profile.test.tsx
□ tag-badge.test.tsx
□ tag-statistics.test.tsx
□ user-search.test.tsx

// Audit 组件
□ audit-card.test.tsx
□ audit-detail.test.tsx
□ review-form.test.tsx
□ event-timeline.test.tsx

// Mock 组件
□ scenario-card.test.tsx
□ manual-generate-form.test.tsx
□ live-event-stream.test.tsx
```

### 5.2 页面集成测试

```typescript
// apps/web/src/app/__tests__/

□ dashboard-page.test.tsx
□ rules-list-page.test.tsx
□ rules-create-page.test.tsx
□ rules-detail-page.test.tsx
□ insight-page.test.tsx
□ insight-user-detail-page.test.tsx
□ audit-page.test.tsx
□ audit-todo-page.test.tsx
□ audit-detail-page.test.tsx
□ mock-page.test.tsx
```

### 5.3 API Mock 策略

```typescript
// apps/web/src/mocks/handlers.ts

export const handlers = [
  // Mock API
  rest.get('/api/mock/health', ...),
  rest.post('/api/mock/generate', ...),
  rest.post('/api/mock/scenario/start', ...),
  
  // Rules API
  rest.get('/api/rules', ...),
  rest.post('/api/rules', ...),
  rest.put('/api/rules/:id', ...),
  rest.delete('/api/rules/:id', ...),
  rest.post('/api/rules/evaluate', ...),
  
  // Insight API
  rest.get('/api/insight/user/:id/tags', ...),
  rest.put('/api/insight/user/:id/tag', ...),
  rest.get('/api/insight/user/:id/profile', ...),
  
  // Audit API
  rest.get('/api/audit/orders', ...),
  rest.post('/api/audit/order', ...),
  rest.put('/api/audit/order/:id/review', ...),
];
```

---

## 6. Phase 4: 端到端用户场景测试 (Playwright)

### 6.1 核心用户场景

#### 场景 1: 规则创建与评估流程
```typescript
test('规则创建到评估完整流程', async ({ page }) => {
  // 1. 登录系统
  await page.goto('/login');
  await page.fill('[name="username"]', 'admin');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');
  
  // 2. 导航到规则页面
  await page.click('text=规则管理');
  await expect(page).toHaveURL('/rules');
  
  // 3. 创建新规则
  await page.click('text=创建规则');
  await page.fill('[name="name"]', '高风险用户检测');
  await page.fill('[name="condition"]', 'event_count > 100');
  await page.click('button[type="submit"]');
  
  // 4. 验证规则创建成功
  await expect(page.locator('text=高风险用户检测')).toBeVisible();
  
  // 5. 执行规则评估
  await page.click('text=评估');
  await page.fill('[name="user_id"]', 'test_user');
  await page.click('button[type="submit"]');
  
  // 6. 验证评估结果
  await expect(page.locator('.evaluation-result')).toBeVisible();
});
```

#### 场景 2: 用户洞察与标签管理
```typescript
test('用户标签管理流程', async ({ page }) => {
  // 1. 搜索用户
  await page.goto('/insight');
  await page.fill('[placeholder="搜索用户"]', 'user_123');
  await page.click('button[type="submit"]');
  
  // 2. 查看用户详情
  await page.click('text=user_123');
  await expect(page).toHaveURL(/\/insight\/user\/user_123/);
  
  // 3. 添加标签
  await page.click('text=编辑标签');
  await page.fill('[name="tag_name"]', 'vip');
  await page.fill('[name="tag_value"]', 'gold');
  await page.click('text=保存');
  
  // 4. 验证标签显示
  await expect(page.locator('text=vip: gold')).toBeVisible();
  
  // 5. 删除标签
  await page.click('.tag-badge:has-text("vip") .delete-btn');
  await expect(page.locator('text=vip: gold')).not.toBeVisible();
});
```

#### 场景 3: 审核工单处理
```typescript
test('审核工单完整处理流程', async ({ page }) => {
  // 1. 查看待处理工单
  await page.goto('/audit/todo');
  const orderCount = await page.locator('.audit-card').count();
  
  // 2. 选择工单
  await page.click('.audit-card:first-child');
  await expect(page).toHaveURL(/\/audit\/order\/.+/);
  
  // 3. 查看事件详情
  await expect(page.locator('.event-timeline')).toBeVisible();
  
  // 4. 填写审核意见
  await page.fill('[name="note"]', '审核通过，用户行为正常');
  await page.click('text=通过');
  
  // 5. 确认操作
  await page.click('text=确认');
  
  // 6. 验证状态变更
  await expect(page.locator('.status-badge:has-text("approved")')).toBeVisible();
  
  // 7. 验证工单列表更新
  await page.goto('/audit/todo');
  await expect(page.locator('.audit-card')).toHaveCount(orderCount - 1);
});
```

#### 场景 4: Mock 事件生成与流处理验证
```typescript
test('事件生成与流处理验证', async ({ page }) => {
  // 1. 导航到 Mock 页面
  await page.goto('/mock');
  
  // 2. 生成测试事件
  await page.fill('[name="count"]', '100');
  await page.click('text=生成事件');
  
  // 3. 验证事件生成成功
  await expect(page.locator('.success-message')).toBeVisible();
  
  // 4. 启动场景
  await page.click('text=场景管理');
  await page.click('text=创建场景');
  await page.selectOption('[name="scenario_type"]', 'normal');
  await page.fill('[name="rate_per_second"]', '10');
  await page.click('text=启动');
  
  // 5. 验证场景运行
  await expect(page.locator('.scenario-status:has-text("running")')).toBeVisible();
  
  // 6. 检查实时事件流
  await page.click('text=实时监控');
  await expect(page.locator('.event-stream')).toBeVisible();
  
  // 7. 停止场景
  await page.click('text=停止');
  await expect(page.locator('.scenario-status:has-text("stopped")')).toBeVisible();
});
```

#### 场景 5: 系统健康检查
```typescript
test('系统健康检查', async ({ page }) => {
  await page.goto('/');
  
  // 验证所有服务状态
  const services = ['Mock', 'Rules', 'Insight', 'Audit', 'Pulsar', 'PostgreSQL', 'Redis'];
  for (const service of services) {
    const statusBadge = page.locator(`.service-status:has-text("${service}") .status-badge`);
    await expect(statusBadge).toHaveClass(/healthy|ok/);
  }
});
```

### 6.2 E2E 测试配置

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5143',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:5143',
    reuseExistingServer: !process.env.CI,
  },
});
```

---

## 7. Phase 5: 性能与压力测试

### 7.1 API 性能基准

```yaml
# 基准要求
Mock API:
  - 事件生成: < 50ms (P99)
  - 场景启动: < 100ms (P99)
  
Rules API:
  - 规则创建: < 50ms (P99)
  - 规则评估: < 10ms (P99)
  - 规则列表: < 100ms (P99, 100条)
  
Insight API:
  - 标签读取: < 20ms (P99, Redis)
  - 用户画像: < 50ms (P99)
  - 批量查询: < 200ms (P99, 100用户)
  
Audit API:
  - 工单创建: < 50ms (P99)
  - 工单列表: < 100ms (P99, 100条)
  - 工单审核: < 50ms (P99)
```

### 7.2 负载测试脚本 (Locust)

```python
# locustfile.py
from locust import HttpUser, task, between

class BehaviorSenseUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_rules(self):
        self.client.get("/api/rules")
    
    @task(2)
    def evaluate_rules(self):
        self.client.post("/api/rules/evaluate", json={
            "context": {"user_id": "test_user", "event_count": 50},
            "execute_actions": False
        })
    
    @task(1)
    def get_user_tags(self):
        self.client.get("/api/insight/user/test_user/tags")
    
    @task(1)
    def list_audit_orders(self):
        self.client.get("/api/audit/orders?status=pending")
    
    @task(1)
    def generate_events(self):
        self.client.post("/api/mock/generate", json={
            "count": 10,
            "user_pool_size": 100
        })
```

### 7.3 压力测试场景

```yaml
# 压力测试配置
场景 1: 正常负载
  - 并发用户: 100
  - 持续时间: 5分钟
  - 目标: 验证系统稳定运行

场景 2: 峰值负载
  - 并发用户: 500
  - 持续时间: 10分钟
  - 目标: 验证系统处理峰值能力

场景 3: 长时间运行
  - 并发用户: 50
  - 持续时间: 1小时
  - 目标: 验证内存泄漏、连接池

场景 4: 事件洪峰
  - Mock 服务生成: 1000 events/s
  - 持续时间: 5分钟
  - 目标: 验证 Stream 处理能力
```

---

## 8. Phase 6: 安全测试

### 8.1 API 安全检查

```yaml
认证与授权:
  □ JWT Token 验证
  □ Token 过期处理
  □ 权限边界验证
  □ 敏感接口鉴权

输入验证:
  □ SQL 注入防护
  □ XSS 防护
  □ 规则条件代码注入防护
  □ 文件上传验证

速率限制:
  □ API 限流验证 (100 req/min)
  □ 并发请求限制
  □ 大文件上传限制

数据安全:
  □ 敏感数据加密
  □ 日志脱敏
  □ 错误信息不暴露内部细节
```

### 8.2 安全测试脚本

```python
# tests/security/test_api_security.py

def test_sql_injection_prevention():
    """测试 SQL 注入防护"""
    response = client.get("/api/insight/user/' OR '1'='1/tags")
    assert response.status_code == 400

def test_xss_prevention():
    """测试 XSS 防护"""
    response = client.post("/api/rules", json={
        "name": "<script>alert('xss')</script>",
        "condition": "true"
    })
    assert "<script>" not in response.json().get("name", "")

def test_rule_code_injection():
    """测试规则条件代码注入"""
    response = client.post("/api/rules/validate", json={
        "condition": "__import__('os').system('ls')"
    })
    assert response.status_code == 400

def test_rate_limiting():
    """测试 API 限流"""
    for i in range(150):
        response = client.get("/api/rules")
        if i >= 100:
            assert response.status_code == 429
```

---

## 9. Phase 7: 上线前检查清单

### 9.1 代码质量

```yaml
代码覆盖率:
  □ 后端单元测试覆盖率 >= 80%
  □ 后端集成测试覆盖率 >= 70%
  □ 前端组件测试覆盖率 >= 60%
  □ E2E 测试覆盖关键用户场景

代码规范:
  □ Ruff 检查通过
  □ ESLint 检查通过
  □ TypeScript 类型检查通过
  □ 无安全漏洞警告

文档:
  □ API 文档完整 (OpenAPI)
  □ README 更新
  □ 部署文档完整
  □ 变更日志更新
```

### 9.2 基础设施

```yaml
容器化:
  □ Docker 镜像构建成功
  □ docker-compose 配置验证
  □ 环境变量配置完整
  □ 日志收集配置

数据库:
  □ 迁移脚本验证
  □ 索引优化完成
  □ 备份策略配置
  □ 连接池配置合理

监控:
  □ Prometheus 指标采集
  □ Grafana 仪表板配置
  □ 告警规则配置
  □ 日志聚合配置
```

### 9.3 性能指标

```yaml
响应时间:
  □ API P99 < 100ms
  □ 页面加载 FCP < 1.8s
  □ 页面加载 LCP < 2.5s

吞吐量:
  □ 支持 500 并发用户
  □ 事件处理 1000 events/s

资源使用:
  □ 内存使用 < 80%
  □ CPU 使用 < 70%
  □ 数据库连接池 < 80%
```

### 9.4 安全检查

```yaml
安全扫描:
  □ 依赖漏洞扫描通过
  □ 镜像安全扫描通过
  □ API 安全测试通过

配置安全:
  □ 敏感信息使用 Secret
  □ 网络隔离配置
  □ HTTPS 配置
  □ CORS 配置正确
```

### 9.5 运维就绪

```yaml
部署:
  □ 部署脚本验证
  □ 回滚流程验证
  □ 蓝绿/金丝雀部署支持

监控告警:
  □ 服务健康检查配置
  □ 资源告警配置
  □ 错误率告警配置
  □ 值班响应流程

应急预案:
  □ 服务宕机恢复
  □ 数据库故障恢复
  □ 消息队列故障恢复
  □ 缓存故障恢复
```

---

## 10. 测试执行计划

### 10.1 时间表

| 阶段 | 任务 | 预计时间 | 负责人 |
|------|------|----------|--------|
| Phase 1 | 基础设施验证 | 1 天 | DevOps |
| Phase 2 | 后端单元测试 | 2 天 | Backend |
| Phase 3 | 后端集成测试 | 2 天 | Backend |
| Phase 4 | 前端组件测试 | 2 天 | Frontend |
| Phase 5 | E2E 测试 | 2 天 | QA |
| Phase 6 | 性能测试 | 1 天 | QA |
| Phase 7 | 安全测试 | 1 天 | Security |
| Phase 8 | 上线检查 | 1 天 | All |

### 10.2 测试环境

```yaml
开发环境:
  - 本地 Docker Compose
  - Mock 模式测试

测试环境:
  - Docker Compose
  - 真实依赖模式
  - CI/CD 自动化

预发布环境:
  - Kubernetes
  - 生产配置
  - 全量测试
```

---

## 11. 测试工具

### 11.1 后端测试

```yaml
框架: pytest + pytest-asyncio
覆盖率: pytest-cov
Mock: pytest-mock
异步测试: pytest-asyncio
HTTP 测试: httpx AsyncClient
```

### 11.2 前端测试

```yaml
单元测试: Jest + React Testing Library
E2E 测试: Playwright
API Mock: MSW (Mock Service Worker)
覆盖率: jest-coverage
```

### 11.3 性能测试

```yaml
负载测试: Locust
APM: Prometheus + Grafana
前端性能: Lighthouse CI
```

---

## 12. 持续集成

### 12.1 CI Pipeline

```yaml
# .github/workflows/test.yml
name: Full Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - name: Run Backend Tests
        run: |
          uv run pytest tests/ --cov --cov-report=xml
      - name: Upload Coverage
        uses: codecov/codecov-action@v3

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Frontend Tests
        run: |
          cd apps/web
          pnpm install
          pnpm test
          pnpm build

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]
    steps:
      - name: Run E2E Tests
        run: |
          cd apps/web
          pnpm install
          pnpm playwright install
          pnpm e2e
```

---

## 附录

### A. 测试数据准备

```python
# scripts/seed_test_data.py

async def seed_test_data():
    """准备测试数据"""
    # 创建测试用户
    for i in range(100):
        await create_user(f"test_user_{i}")
    
    # 创建测试规则
    await create_rule({
        "name": "高频操作检测",
        "condition": "event_count > 100",
        "priority": 10
    })
    
    # 创建测试工单
    for i in range(20):
        await create_audit_order({
            "user_id": f"test_user_{i % 100}",
            "rule_id": "test_rule_001"
        })
```

### B. 测试报告模板

```markdown
# 测试执行报告

## 执行摘要
- 执行日期: YYYY-MM-DD
- 测试环境: staging
- 总用例数: XXX
- 通过数: XXX
- 失败数: XXX
- 阻塞数: XXX

## 覆盖率报告
- 后端单元测试: XX%
- 后端集成测试: XX%
- 前端组件测试: XX%
- E2E 测试: XX 场景通过

## 性能报告
- API 平均响应时间: XXms
- P99 响应时间: XXms
- 最大并发用户: XXX

## 缺陷统计
| 严重程度 | 数量 | 状态 |
|---------|------|------|
| Critical | X | X |
| Major | X | X |
| Minor | X | X |

## 风险与建议
1. ...
2. ...
```

---

**文档版本**: 1.0
**最后更新**: 2026-04-05
