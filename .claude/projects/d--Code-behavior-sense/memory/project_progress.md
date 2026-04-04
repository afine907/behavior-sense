---
name: project_progress
description: BehaviorSense 项目开发进度和功能完成状态
type: project
---

# 项目开发进度

## 总体状态: 🟢 核心功能完成 + Monorepo 重构完成 + CI修复完成

**最后更新**: 2026-04-04
**重大变更**: CI lint/test/mypy 全部通过，Docker构建改用GitHub Registry

---

## 2026-04-04 更新

### CI 修复
- [x] 修复 ruff lint 错误 (import排序、行长度、未使用变量)
- [x] 修复 mypy 类型错误 (添加类型注解、配置宽松模式)
- [x] 修复测试错误 (EventType枚举检查、随机种子隔离)
- [x] Docker构建改用 GitHub Container Registry (ghcr.io)

### Monorepo 重构
- [x] 迁移到标准 monorepo 目录结构 (`libs/`, `packages/`, `apps/`, `infrastructure/`)
- [x] 所有 Python 包采用 `src/` 标准布局
- [x] 配置 uv workspace 管理多包依赖
- [x] 更新 CI/CD 使用 `astral-sh/setup-uv@v3`
- [x] 更新 Dockerfile 支持 uv 和多服务构建
- [x] 创建前端 `apps/web/` 目录 (预留)

### 测试覆盖
- [x] 添加单元测试 (test_core, test_audit, test_insight, test_mock, test_rules, test_stream)
- [x] 测试覆盖率报告
- [x] 修复发现的 bug (规则引擎、窗口操作)

### QA 评估 Skill
- [x] 添加全栈效果评估 Skill (`.claude/skills/qa-evaluator/`)
- [x] 支持前端、后端、全栈三种评估模式
- [x] 配置 MCP 工具集成

---

## 模块完成状态

### ✅ 已完成模块

| 模块 | 状态 | 说明 |
|------|------|------|
| libs/core | ✅ 完成 | 核心数据模型、配置管理、安全模块、中间件、指标 |
| packages/mock | ✅ 完成 | 用户行为模拟器、Pulsar 生产者 |
| packages/stream | ✅ 完成 | Faust 应用、聚合任务、模式检测、窗口函数 |
| packages/rules | ✅ 完成 | 规则引擎(AST解析)、规则加载器、动作处理器 |
| packages/insight | ✅ 完成 | 标签服务、用户画像、API 路由 |
| packages/audit | ✅ 完成 | 审核服务、状态机、API 路由 |

### ✅ 已完成配置

| 配置项 | 状态 | 说明 |
|--------|------|------|
| pyproject.toml | ✅ 完成 | uv workspace 配置 |
| uv.lock | ✅ 完成 | 依赖锁定 |
| pnpm-workspace.yaml | ✅ 完成 | 前端 workspace |
| docker-compose.yml | ✅ 完成 | 开发环境配置 |
| Dockerfile | ✅ 完成 | 多服务构建支持 |
| CI/CD | ✅ 完成 | GitHub Actions + uv |

---

## 🟡 待完善功能

### 功能增强
- [ ] 数据库迁移脚本 (Alembic)
- [ ] 端到端测试
- [ ] 规则热更新原子性优化

### 前端开发
- [ ] Next.js 应用初始化
- [ ] 用户行为可视化 Dashboard
- [ ] 实时大屏

### 运维部署
- [ ] Kubernetes Helm Chart
- [ ] 生产环境配置
- [ ] 告警规则配置

---

## Why:
- 记录项目当前进度，方便后续继续开发
- Monorepo 结构为后续前端集成做好准备
- uv 包管理提升开发效率和 CI 速度

## How to apply:
- 继续开发时先检查此文件了解当前状态
- 使用 `uv sync` 安装依赖，`uv run pytest` 运行测试
- 前端代码放入 `apps/` 目录
