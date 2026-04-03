# BehaviorSense 编码计划

## 项目概览

基于 Wiki 知识库，使用多 Agent 并行开发 BehaviorSense 项目。

## 任务依赖图

```
                    ┌─────────────┐
                    │ Phase 0     │
                    │ 项目初始化   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Phase 1     │
                    │ behavior_core│
                    │ (核心库)     │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
   │ Phase 2A    │  │ Phase 2B    │  │ Phase 2C    │
   │ behavior    │  │ behavior    │  │ behavior    │
   │ _mock       │  │ _stream     │  │ _rules      │
   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌──────▼──────┐        │
   │ Phase 3A    │  │ Phase 3B    │        │
   │ behavior    │  │ behavior    │        │
   │ _insight    │  │ _audit      │        │
   └──────┬──────┘  └──────┬──────┘        │
          │                │                │
          └────────────────┼────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Phase 4     │
                    │ 集成测试     │
                    │ Docker部署   │
                    └─────────────┘
```

---

## Phase 0: 项目初始化 (优先级: P0)

### 任务清单

| 任务 | 描述 | 状态 |
|------|------|------|
| 0.1 | 创建项目目录结构 | ⬜ |
| 0.2 | 创建 pyproject.toml | ⬜ |
| 0.3 | 创建 .env.example | ⬜ |
| 0.4 | 创建 docker-compose.yml | ⬜ |
| 0.5 | 创建 README.md | ⬜ |

### 目录结构

```
behavior-sense/
├── pyproject.toml
├── README.md
├── .env.example
├── docker-compose.yml
├── behavior_core/
├── behavior_mock/
├── behavior_stream/
├── behavior_rules/
├── behavior_insight/
├── behavior_audit/
├── tests/
└── docker/
```

---

## Phase 1: behavior_core 核心库 (优先级: P0)

### 依赖关系
- 无依赖，是所有模块的基础

### 任务清单

| 任务 | 描述 | 状态 |
|------|------|------|
| 1.1 | 创建数据模型 (models/event.py, user.py) | ⬜ |
| 1.2 | 创建配置管理 (config/settings.py) | ⬜ |
| 1.3 | 创建日志工具 (utils/logging.py) | ⬜ |
| 1.4 | 创建时间工具 (utils/datetime.py) | ⬜ |
| 1.5 | 编写单元测试 | ⬜ |

### 输出文件

```
behavior_core/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── event.py
│   └── user.py
├── config/
│   ├── __init__.py
│   └── settings.py
└── utils/
    ├── __init__.py
    ├── logging.py
    └── datetime.py
```

---

## Phase 2A: behavior_mock 模拟器 (优先级: P1)

### 依赖关系
- 依赖 behavior_core

### 任务清单

| 任务 | 描述 | 状态 |
|------|------|------|
| 2A.1 | 创建行为生成器 (generator.py) | ⬜ |
| 2A.2 | 创建 Pulsar 生产者 (producer.py) | ⬜ |
| 2A.3 | 创建场景配置 (scenarios.py) | ⬜ |
| 2A.4 | 创建 FastAPI 入口 (main.py) | ⬜ |
| 2A.5 | 编写单元测试 | ⬜ |

### 输出文件

```
behavior_mock/
├── __init__.py
├── main.py
├── generator.py
├── producer.py
└── scenarios.py
```

---

## Phase 2B: behavior_stream 流处理 (优先级: P1)

### 依赖关系
- 依赖 behavior_core

### 任务清单

| 任务 | 描述 | 状态 |
|------|------|------|
| 2B.1 | 创建 Faust 应用 (app.py) | ⬜ |
| 2B.2 | 创建聚合任务 (jobs/aggregation.py) | ⬜ |
| 2B.3 | 创建模式检测 (jobs/detection.py) | ⬜ |
| 2B.4 | 创建窗口函数 (operators/window.py) | ⬜ |
| 2B.5 | 创建入口 (main.py) | ⬜ |
| 2B.6 | 编写单元测试 | ⬜ |

### 输出文件

```
behavior_stream/
├── __init__.py
├── main.py
├── app.py
├── jobs/
│   ├── __init__.py
│   ├── aggregation.py
│   └── detection.py
└── operators/
    ├── __init__.py
    └── window.py
```

---

## Phase 2C: behavior_rules 规则引擎 (优先级: P1)

### 依赖关系
- 依赖 behavior_core

### 任务清单

| 任务 | 描述 | 状态 |
|------|------|------|
| 2C.1 | 创建规则模型 (models.py) | ⬜ |
| 2C.2 | 创建规则引擎 (engine.py) | ⬜ |
| 2C.3 | 创建规则加载器 (loader.py) | ⬜ |
| 2C.4 | 创建动作处理器 (actions/tagging.py, audit.py) | ⬜ |
| 2C.5 | 创建 FastAPI 入口 (main.py) | ⬜ |
| 2C.6 | 编写单元测试 | ⬜ |

### 输出文件

```
behavior_rules/
├── __init__.py
├── main.py
├── models.py
├── engine.py
├── loader.py
└── actions/
    ├── __init__.py
    ├── tagging.py
    └── audit.py
```

---

## Phase 3A: behavior_insight 洞察服务 (优先级: P2)

### 依赖关系
- 依赖 behavior_core
- 依赖 behavior_rules (动作处理)

### 任务清单

| 任务 | 描述 | 状态 |
|------|------|------|
| 3A.1 | 创建标签服务 (services/tag_service.py) | ⬜ |
| 3A.2 | 创建用户仓库 (repositories/user_repo.py) | ⬜ |
| 3A.3 | 创建标签 API (routers/tags.py) | ⬜ |
| 3A.4 | 创建画像 API (routers/profile.py) | ⬜ |
| 3A.5 | 创建 FastAPI 入口 (main.py) | ⬜ |
| 3A.6 | 编写单元测试 | ⬜ |

### 输出文件

```
behavior_insight/
├── __init__.py
├── main.py
├── routers/
│   ├── __init__.py
│   ├── tags.py
│   └── profile.py
├── services/
│   ├── __init__.py
│   └── tag_service.py
└── repositories/
    ├── __init__.py
    └── user_repo.py
```

---

## Phase 3B: behavior_audit 审核服务 (优先级: P2)

### 依赖关系
- 依赖 behavior_core
- 依赖 behavior_rules (触发审核)

### 任务清单

| 任务 | 描述 | 状态 |
|------|------|------|
| 3B.1 | 创建审核服务 (services/audit_service.py) | ⬜ |
| 3B.2 | 创建审核仓库 (repositories/audit_repo.py) | ⬜ |
| 3B.3 | 创建审核 API (routers/audit.py) | ⬜ |
| 3B.4 | 创建 FastAPI 入口 (main.py) | ⬜ |
| 3B.5 | 编写单元测试 | ⬜ |

### 输出文件

```
behavior_audit/
├── __init__.py
├── main.py
├── routers/
│   ├── __init__.py
│   └── audit.py
├── services/
│   ├── __init__.py
│   └── audit_service.py
└── repositories/
    ├── __init__.py
    └── audit_repo.py
```

---

## Phase 4: 集成测试与部署 (优先级: P3)

### 任务清单

| 任务 | 描述 | 状态 |
|------|------|------|
| 4.1 | 创建 Dockerfile | ⬜ |
| 4.2 | 完善 docker-compose.yml | ⬜ |
| 4.3 | 编写集成测试 | ⬜ |
| 4.4 | 编写端到端测试 | ⬜ |
| 4.5 | 创建 GitHub Actions CI | ⬜ |

---

## Agent 调度策略

### 并行执行规则

```
Phase 0 (串行) → 完成后
    ↓
Phase 1 (串行) → 完成后
    ↓
Phase 2A, 2B, 2C (并行) → 全部完成后
    ↓
Phase 3A, 3B (并行) → 全部完成后
    ↓
Phase 4 (串行)
```

### Agent 分配

| Agent | 负责任务 |
|-------|----------|
| Agent-Init | Phase 0, Phase 1 (项目初始化+核心库) |
| Agent-Mock | Phase 2A (模拟器) |
| Agent-Stream | Phase 2B (流处理) |
| Agent-Rules | Phase 2C (规则引擎) |
| Agent-Insight | Phase 3A (洞察服务) |
| Agent-Audit | Phase 3B (审核服务) |
| Agent-Deploy | Phase 4 (部署集成) |

---

## 预计时间

| 阶段 | 预计时间 | 并行度 |
|------|----------|--------|
| Phase 0 | 10 分钟 | 1 |
| Phase 1 | 20 分钟 | 1 |
| Phase 2 | 30 分钟 | 3 (并行) |
| Phase 3 | 20 分钟 | 2 (并行) |
| Phase 4 | 15 分钟 | 1 |
| **总计** | **~60 分钟** | - |

---

## 执行命令

开始执行编码计划，使用以下命令：

```
请按照 PLAN.md 开始执行编码任务
```

或者分阶段执行：

```
请执行 Phase 0 项目初始化
请执行 Phase 1 behavior_core
请并行执行 Phase 2A, 2B, 2C
请并行执行 Phase 3A, 3B
请执行 Phase 4 集成部署
```