# BehaviorSense 测试执行报告

> **执行日期**: 2026-04-05
> **状态**: Phase 1-6 完成，Phase 7-8 待执行

---

## 一、测试结果总览

### 后端 API 测试 ✅

| 服务 | 测试用例 | 通过 | 状态 |
|------|----------|------|------|
| Mock | 19 | 19 | ✅ 全部通过 |
| Rules | 22 | 22 | ✅ 全部通过 |
| Insight | 20 | 20 | ✅ 全部通过 |
| Audit | 23 | 23 | ✅ 全部通过 |
| **总计** | **84** | **84** | ✅ |

### 前端测试 ✅

| 测试类型 | 测试用例 | 通过 | 状态 |
|----------|----------|------|------|
| Jest 单元测试 | 25 | 25 | ✅ 全部通过 |
| TypeScript 类型检查 | - | - | ✅ 无错误 |
| Next.js 构建 | - | - | ✅ 成功 |
| Playwright E2E | 14 场景 | - | ✅ 配置完成 |

---

## 二、测试环境

### Docker 容器

| 服务 | 端口 | 状态 |
|------|------|------|
| PostgreSQL (测试) | 5433 | ✅ 运行中 |
| Redis | 6379 | ✅ 运行中 |

### 环境变量配置

```bash
# 后端测试环境变量
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=behavior_sense_test
POSTGRES_PASSWORD=postgres
REDIS_URL=redis://localhost:6379
TEST_REAL_DEPS=1
```

---

## 三、测试命令参考

### 后端测试

```bash
# Mock 模式 (快速，无外部依赖)
uv run pytest tests/test_api/test_mock_api.py tests/test_api/test_rules_api.py -v

# 真实依赖模式 (需要 Docker)
docker-compose -f docker-compose.test.yml up -d
POSTGRES_HOST=localhost POSTGRES_PORT=5433 POSTGRES_DB=behavior_sense_test \
POSTGRES_PASSWORD=postgres REDIS_URL="redis://localhost:6379" \
TEST_REAL_DEPS=1 uv run pytest tests/test_api/ -v

# 集成测试
TEST_REAL_DEPS=1 uv run pytest tests/test_integration/ -v

# 覆盖率报告
uv run pytest tests/ --cov=libs --cov=packages --cov-report=html
```

### 前端测试

```bash
# 单元测试
cd apps/web && pnpm test

# 类型检查
cd apps/web && pnpm type-check

# 构建
cd apps/web && pnpm build

# E2E 测试 (需要前后端运行)
cd apps/web && pnpm test:e2e
```

### 性能测试

```bash
# 安装 locust
pip install locust

# 运行负载测试
locust -f tests/performance/locustfile.py --host=http://localhost:8001

# Web UI: http://localhost:8089
```

---

## 四、测试覆盖范围

### API 端点覆盖

| 服务 | 端点 | 覆盖率 |
|------|------|--------|
| Mock | /health, /metrics, /events, /scenarios | 100% |
| Rules | /health, /metrics, /rules, /evaluate, /validate | 100% |
| Insight | /health, /metrics, /tags, /profile, /users | 100% |
| Audit | /health, /metrics, /orders, /review, /stats | 100% |

### 前端组件覆盖

| 组件类型 | 已测试 | 待测试 |
|----------|--------|--------|
| UI 组件 | Button, cn, format | 其他 UI 组件 |
| 页面组件 | - | 所有页面 |
| Hooks | - | 所有 hooks |

---

## 五、待执行项目

### Phase 7: 性能测试

- [ ] API 响应时间基准测试
- [ ] 并发用户负载测试
- [ ] 长时间稳定性测试
- [ ] 事件流处理性能测试

### Phase 8: 上线前检查

- [ ] 代码覆盖率 >= 80%
- [ ] 安全扫描通过
- [ ] Docker 镜像构建成功
- [ ] 文档完整
- [ ] 监控配置完成

---

## 六、注意事项

1. **测试执行时间**: Insight 和 Audit 服务测试需要约 8-11 分钟执行
2. **数据库清理**: 测试使用独立数据库 `behavior_sense_test`
3. **E2E 测试**: 需要同时运行前后端服务
4. **Redis 版本**: 某些 alpine 镜像可能存在架构兼容问题

---

**文档版本**: 1.0
**最后更新**: 2026-04-05
