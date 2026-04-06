# BehaviorSense 测试报告

## 测试概览

**测试日期**: 2026-04-05
**测试工具**: pytest + httpx (后端), Jest + RTL (前端), Playwright (E2E)
**总测试用例**: 109+ 个

## 测试结果汇总

### 后端 API 测试 (84 passed)

| 服务 | 测试用例 | 通过 | 失败 | 状态 |
|------|----------|------|------|------|
| Mock | 19 | 19 | 0 | ✅ 全部通过 |
| Rules | 22 | 22 | 0 | ✅ 全部通过 |
| Insight | 21 | 21 | 0 | ✅ 全部通过 |
| Audit | 22 | 22 | 0 | ✅ 全部通过 |
| **总计** | **84** | **84** | **0** | ✅ 全部通过 |

### 前端单元测试 (25 passed)

| 测试模块 | 测试用例 | 通过 | 状态 |
|----------|----------|------|------|
| utils (cn, format) | 12 | 12 | ✅ |
| UI Components (Button) | 13 | 13 | ✅ |
| **总计** | **25** | **25** | ✅ |

### E2E 测试 (Playwright)

| 测试场景 | 状态 |
|----------|------|
| 登录流程 | ✅ 已配置 |
| Dashboard 服务状态 | ✅ 已配置 |
| 规则管理 | ✅ 已配置 |
| 审核工作流 | ✅ 已配置 |
| 用户洞察 | ✅ 已配置 |
| Mock 数据生成 | ✅ 已配置 |

## 详细测试结果

### 一、Mock 服务 (19/19 通过) ✅

#### 健康检查 (1/1)
- `test_health_check` - 通过

#### 事件生成 (5/5)
- `test_generate_events_default` - 通过
- `test_generate_events_with_event_types` - 通过
- `test_generate_events_weighted` - 通过
- `test_generate_events_invalid_type` - 通过
- `test_generate_events_count_limit` - 通过

#### 场景管理 (13/13)
- `test_start_normal_scenario` - 通过
- `test_start_flash_sale_scenario` - 通过
- `test_start_abnormal_scenario` - 通过
- `test_start_gradual_scenario` - 通过
- `test_start_invalid_scenario_type` - 通过
- `test_list_scenarios` - 通过
- `test_get_scenario_info` - 通过
- `test_get_nonexistent_scenario` - 通过
- `test_stop_scenario` - 通过
- `test_pause_and_resume_scenario` - 通过
- `test_delete_scenario` - 通过
- `test_delete_running_scenario` - 通过
- `test_duplicate_scenario_id` - 通过

### 二、Rules 服务 (22/22 通过) ✅

#### 健康检查 (3/3)
- `test_health_check` - 通过
- `test_readiness_check` - 通过
- `test_metrics_endpoint` - 通过

#### 规则 CRUD (13/13)
- `test_list_rules_empty` - 通过
- `test_create_rule` - 通过
- `test_create_rule_minimal` - 通过
- `test_create_rule_invalid` - 通过
- `test_get_rule` - 通过
- `test_get_nonexistent_rule` - 通过
- `test_update_rule` - 通过
- `test_update_nonexistent_rule` - 通过
- `test_delete_rule` - 通过
- `test_delete_nonexistent_rule` - 通过
- `test_list_rules_with_pagination` - 通过
- `test_list_rules_filter_enabled` - 通过
- `test_list_rules_filter_tag` - 通过

#### 规则评估 (5/5)
- `test_evaluate_rules` - 通过
- `test_evaluate_specific_rules` - 通过
- `test_dry_run_evaluate` - 通过
- `test_validate_rule_condition` - 通过
- `test_validate_invalid_condition` - 通过

#### 规则统计 (1/1)
- `test_get_stats` - 通过

### 三、Insight 服务 (21/21 通过) ✅

**状态**: 已修复时区问题，全部通过

#### 健康检查 (3/3)
- `test_health_check` - 通过
- `test_metrics_endpoint` - 通过
- `test_root_endpoint` - 通过

#### 标签管理 (8/8)
- `test_update_user_tag` - 通过
- `test_get_user_tags` - 通过
- `test_get_nonexistent_user_tags` - 通过
- `test_delete_user_tag` - 通过
- `test_delete_nonexistent_tag` - 通过
- `test_batch_get_tags` - 通过
- `test_batch_get_tags_too_many_users` - 通过
- `test_get_users_by_tag` - 通过

#### 用户画像 (10/10)
- `test_get_user_profile_not_found` - 通过
- `test_update_user_profile` - 通过
- `test_get_user_profile` - 通过
- `test_get_user_stat_not_found` - 通过
- `test_get_users_by_risk` - 通过
- `test_get_users_by_invalid_risk` - 通过
- `test_delete_user` - 通过
- `test_delete_nonexistent_user` - 通过
- `test_get_tag_statistics` - 通过

### 四、Audit 服务 (22/22 通过) ✅

**状态**: 已修复数据库初始化问题，全部通过

#### 健康检查 (3/3)
- `test_health_check` - 通过
- `test_metrics_endpoint` - 通过
- `test_root_endpoint` - 通过

#### 工单管理 (10/10)
- `test_create_order` - 通过
- `test_create_order_minimal` - 通过
- `test_create_order_invalid_level` - 通过
- `test_get_order` - 通过
- `test_get_nonexistent_order` - 通过
- `test_assign_order` - 通过
- `test_assign_nonexistent_order` - 通过
- `test_submit_review_approve` - 通过
- `test_submit_review_reject` - 通过
- `test_reopen_order` - 通过
- `test_delete_order` - 通过
- `test_delete_nonexistent_order` - 通过

#### 列表查询 (6/6)
- `test_list_orders` - 通过
- `test_list_orders_with_pagination` - 通过
- `test_list_orders_filter_status` - 通过
- `test_list_orders_filter_assignee` - 通过
- `test_get_todo_orders` - 通过
- `test_get_unassigned_orders` - 通过

#### 批量操作 (1/1)
- `test_batch_assign` - 通过

#### 统计 (1/1)
- `test_get_stats` - 通过

---

## 修复的问题

### 第二轮迭代修复 (2026-04-05)

#### 1. Insight 服务时区问题
- **问题**: 数据库使用 `TIMESTAMP WITHOUT TIME ZONE`，但代码传入带时区的 `datetime`
- **原因**: 代码使用 `datetime.now(timezone.utc)` 传入带时区的 datetime
- **修复**: 创建 `utcnow_naive()` 函数，返回无时区信息的 UTC 时间

#### 2. Audit 服务数据库初始化问题
- **问题**: Fixture 手动初始化数据库，但应用 lifespan 未正确触发
- **原因**: `ASGITransport` 不会自动执行 FastAPI 的 lifespan
- **修复**: 创建 `_lifespan_manager` 上下文管理器，手动管理应用生命周期

#### 3. Insight 服务用户仓库依赖问题
- **问题**: `get_user_repo` 使用 `request.app.state.user_repo`，但 middleware 设置的是 `request.state.user_repo`
- **原因**: 依赖注入路径不一致
- **修复**: 更新 `get_user_repo` 优先使用 `request.state`，否则回退到 `app.state`

#### 4. datetime.utcnow() 弃用警告
- **问题**: `datetime.utcnow()` 在 Python 3.12+ 中已弃用
- **原因**: 多处使用已弃用的 API
- **修复**: 统一使用 `datetime.now(timezone.utc).replace(tzinfo=None)`

### 第一轮迭代修复

#### 1. Mock 服务场景启动状态问题
- **问题**: 场景启动后状态返回 `idle` 而非 `running`
- **原因**: `start()` 方法在 `stream()` generator 内部调用，但响应返回时 generator 还没开始迭代
- **修复**: 在 API 层面显式调用 `scenario.start()` 方法

#### 2. Mock 服务后台任务阻塞问题
- **问题**: 后台任务使用 `BackgroundTasks` 导致请求阻塞 60 秒
- **原因**: TestClient 中 `BackgroundTasks` 同步执行，阻塞响应
- **修复**: 改用 `asyncio.create_task()` 异步执行后台任务

#### 3. Mock 服务场景状态自动完成问题
- **问题**: 场景状态意外变成 `completed`
- **原因**: `stream()` 的 `finally` 块在 generator 结束时自动设置状态
- **修复**: 移除 `finally` 块中的自动状态设置逻辑

#### 4. Rules 服务统计接口路由问题
- **问题**: `/api/rules/stats` 返回 404
- **原因**: 路由定义顺序问题，`/api/rules/stats` 被 `/api/rules/{rule_id}` 匹配
- **修复**: 将 `/api/rules/stats` 路由移到 `/api/rules/{rule_id}` 之前定义

---

## 测试环境要求

### 运行完整测试套件需要：

1. **Python 3.11+**
2. **uv 包管理器**
3. **Redis 服务器** (用于 Insight 和 Audit 服务)
4. **PostgreSQL 数据库** (用于 Insight 和 Audit 服务)

### 启动依赖服务

```bash
# 使用 Docker 启动依赖服务
docker run -d --name redis -p 6379:6379 redis:alpine
docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15

# 设置环境变量
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/behavior_sense"
export REDIS_URL="redis://localhost:6379/0"
```

### 运行测试

```bash
# 运行所有测试
uv run pytest tests/test_api/ -v

# 只运行 Mock 和 Rules 测试（无需外部依赖）
uv run pytest tests/test_api/test_mock_api.py tests/test_api/test_rules_api.py -v
```

---

## 建议的下一步

1. **配置 CI/CD**: 在 CI 环境中使用 Docker Compose 启动依赖服务 ✅ 已完成
2. **性能测试**: 添加 API 性能测试和压力测试

---

## 集成测试实现 (2026-04-05)

### 测试架构

采用**双模式测试架构**，支持快速迭代和生产验证：

| 模式 | 外部依赖 | 用途 | 运行命令 |
|------|----------|------|----------|
| Mock 模式 | 无 | 快速迭代开发 | `uv run pytest tests/test_api/test_mock_api.py tests/test_api/test_rules_api.py tests/test_integration/test_basic_integration.py -v` |
| 真实依赖模式 | Redis + PostgreSQL | CI 验证、生产前检查 | `TEST_REAL_DEPS=1 uv run pytest tests/ -v` |

### 测试文件结构

```
tests/test_integration/
├── conftest.py                      # 集成测试 fixtures（Mock 模式 + 真实依赖模式）
├── test_basic_integration.py        # 基础集成测试（Mock 模式，51 用例）
├── test_http_integration.py         # HTTP 服务间调用测试（真实依赖）
├── test_e2e_user_tagging.py         # 端到端：用户打标签流程
├── test_e2e_audit_flow.py           # 端到端：审核流程
├── test_state_consistency.py        # 状态一致性验证
└── test_integration.py              # 原有集成测试
```

### 测试覆盖范围

| 测试文件 | 测试数量 | Mock 模式 | 真实依赖模式 |
|----------|----------|-----------|--------------|
| test_mock_api.py | 19 | ✅ | ✅ |
| test_rules_api.py | 22 | ✅ | ✅ |
| test_insight_api.py | 21 | ❌ | ✅ |
| test_audit_api.py | 22 | ❌ | ✅ |
| test_basic_integration.py | 10 | ✅ | ✅ |
| **总计** | **94** | **51** | **94** |

### 运行测试

```bash
# Mock 模式（快速，无外部依赖）
uv run pytest tests/test_api/test_mock_api.py tests/test_api/test_rules_api.py tests/test_integration/test_basic_integration.py -v

# 真实依赖模式（需要 Docker）
docker-compose -f docker-compose.test.yml up -d
TEST_REAL_DEPS=1 uv run pytest tests/ -v
docker-compose -f docker-compose.test.yml down -v

# 使用脚本运行
./scripts/run_tests.sh           # Mock 模式
./scripts/run_tests.sh --real    # 真实依赖模式
./scripts/run_tests.sh --all     # 所有测试
```

### CI/CD 配置

CI 流程包含两个测试阶段：

1. **test-mock**: 快速反馈，无外部依赖，每次提交运行
2. **test-integration**: 完整验证，使用 GitHub Actions 服务容器

```yaml
# .github/workflows/ci.yml
jobs:
  test-mock:
    # 快速测试，无需外部依赖
  test-integration:
    # 使用 PostgreSQL + Redis 服务容器
    services:
      postgres: ...
      redis: ...
```

### 关键文件

| 文件 | 用途 |
|------|------|
| `tests/test_integration/conftest.py` | Mock Redis、内存数据库、双模式 fixture |
| `docker-compose.test.yml` | 测试专用 Docker Compose 配置 |
| `scripts/run_tests.sh` | 测试运行脚本 |
| `.github/workflows/ci.yml` | CI 配置 |

### 测试内容

#### 基础集成测试 (test_basic_integration.py)

- **Rules 服务集成测试**
  - 规则 CRUD 完整流程
  - 规则评估流程
  - 规则条件验证
  - 规则统计

- **Mock 服务集成测试**
  - 事件生成流程
  - 场景管理流程

- **跨服务规则评估测试**
  - 规则评估触发打标签动作（dry-run）
  - 规则评估触发审核动作（dry-run）

- **直接模块集成测试**
  - 事件生成器到规则引擎的数据流
  - 规则引擎优先级排序
