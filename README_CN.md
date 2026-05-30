<h1 align="center">
  <br>
  <a href="#"><img src="https://via.placeholder.com/200x200?text=BS" alt="BehaviorSense" width="120"></a>
  <br>
  BehaviorSense
  <br>
</h1>

<h4 align="center">🔍 实时 AI Agent 行为分析平台</h4>

<p align="center">
  实时监控、分析和治理 AI Agent 行为，内置 12 个异常检测器。
</p>

<p align="center">
  <a href="#-为什么选择-behaviorsense">为什么</a> •
  <a href="#-核心功能">功能</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-架构设计">架构</a> •
  <a href="#-api-文档">API</a> •
  <a href="#-贡献指南">贡献</a>
</p>

<p align="center">
  <a href="https://github.com/afine907/behavior-sense/actions/workflows/ci.yml">
    <img src="https://github.com/afine907/behavior-sense/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  </a>
  <a href="https://docs.astral.sh/ruff/">
    <img src="https://img.shields.io/badge/code%20style-ruff-orange.svg" alt="Code style: ruff">
  </a>
  <a href="https://github.com/afine907/behavior-sense/stargazers">
    <img src="https://img.shields.io/github/stars/afine907/behavior-sense.svg?style=social" alt="GitHub Stars">
  </a>
</p>

<p align="center">
  <a href="README.md">English</a> | <a href="README_CN.md">中文</a>
</p>

---

## 🎯 什么是 BehaviorSense？

**BehaviorSense** 是一个开源的实时 AI Agent 行为分析平台。它以亚秒级延迟监控、分析和治理自主 AI Agent 系统。

随着团队部署能够调用工具、消耗 Token 和与系统交互的 AI Agent，可见性变得至关重要。BehaviorSense 提供：

- **🔍 完整执行追踪** - 跟踪每个 Agent 操作、工具调用和决策
- **🚨 12 个异常检测器** - 捕获成本飙升、Prompt 注入、死循环等
- **📊 多维度评分** - 量化 Agent 行为风险
- **🛡️ 热重载防护栏** - 基于 YAML 的规则，无需重启
- **👥 人在回路中** - 内置审计工作流，用于高风险决策
- **🔗 多 Agent 图** - 可视化 Agent 交互和依赖关系

```
Agent 操作 → 流处理 → 检测 → 自动标记 / 提交审计
     ↓         < 1 秒        ↓
  [Pulsar] ──→ [Stream] ──→ [决策] ──→ [动作]
```

---

## 💡 为什么选择 BehaviorSense？

| 痛点 | BehaviorSense 解决方案 |
|------|------------------------|
| **无法看到 Agent 工具调用** | 完整执行追踪，包含延迟和成本分解 |
| **Token 成本失控** | 实时成本异常检测，每个 Agent 预算 |
| **Prompt 注入未被检测** | 基于 AST 的 Prompt 分析，即时捕获注入模式 |
| **多 Agent 系统不透明** | 关联引擎跨 Agent 工作流链接操作 |
| **防护栏需要代码更改** | 热重载安全规则（YAML）— 无需重新部署 |
| **难以审计自主决策** | 内置人在回路中的审计工作流 |

### 🏆 与 Langfuse / Phoenix / LangSmith 对比

| 功能 | BehaviorSense | Langfuse | Phoenix | LangSmith |
|------|---------------|----------|---------|-----------|
| **实时异常检测** | ✅ 12 个检测器 | ❌ | 🔶 基础 | ❌ |
| **规则引擎** | ✅ AST 安全，热重载 | ❌ | ❌ | ❌ |
| **成本优化** | ✅ 内置建议 | 🔶 基础 | 🔶 基础 | ✅ |
| **多 Agent 图** | ✅ 依赖分析 | ❌ | ❌ | ❌ |
| **行为回放** | ✅ 单步执行 | ❌ | ❌ | ❌ |
| **合规检查** | ✅ 8 条规则 | ❌ | ❌ | ❌ |
| **Prompt 管理** | ✅ 版本控制 | ✅ | ❌ | ✅ |
| **OTel 集成** | ✅ 原生 | ✅ | ✅ | ❌ |
| **框架集成** | ✅ LangChain, LlamaIndex, OpenAI | ✅ | ✅ | ✅ LangChain |
| **自托管** | ✅ MIT 许可证 | ✅ MIT | 🔶 Elastic 2.0 | ❌ 仅 SaaS |
| **许可证** | MIT | MIT | Elastic 2.0 | 专有 |

---

## ✨ 核心功能

### 🚨 12 个异常检测器

| 检测器 | 检测目标 | 阈值 |
|--------|----------|------|
| **AgentLoopDetector** | 死循环 | 60 秒内 5+ 次相同操作 |
| **CostSpikeDetector** | 成本飙升 | 每 Agent >$10/分钟 |
| **TokenExplosionDetector** | Token 爆炸 | 10 秒内 >10K Token |
| **ToolAbuseDetector** | 工具滥用 | >50 次调用/分钟 |
| **TimeoutCascadeDetector** | 超时级联 | 5 分钟内 3+ 次超时 |
| **CapabilityDriftDetector** | 能力漂移 | 新工具使用模式 |
| **MultiAgentContentionDetector** | 资源争用 | 协调资源访问 |
| **PromptInjectionDetector** | Prompt 注入 | 多个注入指标 |
| **DataExfiltrationDetector** | 数据泄露 | 输出中的敏感数据 |
| **HallucinationDetector** | 幻觉 | 低置信度 + 模糊语言 |
| **CostExplosionDetector** | 舰队成本爆炸 | 舰队整体 >$100/分钟 |
| **AgentCollusionDetector** | Agent 串通 | 过度双边通信 |

### 🛡️ 规则引擎

```yaml
# rules/agent_guardrails.yaml
- name: "高 Token 成本告警"
  condition: "token_cost > 5.00 and agent_role != 'planner'"
  priority: 10
  actions:
    - type: TAG_AGENT
      params: { tags: ["cost_anomaly"] }
    - type: TRIGGER_AUDIT
      params: { level: "high" }

- name: "检测到 Prompt 注入"
  condition: "injection_score > 0.85"
  priority: 1
  actions:
    - type: BLOCK_EXECUTION
      params: { reason: "injection_detected" }
    - type: TRIGGER_AUDIT
      params: { level: "critical" }
```

**支持热重载** — 修改防护栏无需重启

### 📊 Agent 分析

- **Agent 画像** - 能力、历史、风险评估
- **成本跟踪** - 每个 Agent 和舰队整体成本监控
- **性能指标** - 延迟、成功率、错误率
- **行为模式** - 循环检测、升级、交替
- **优化建议** - 成本、性能、工具使用
- **合规检查** - 安全、成本、工具、隐私策略

### 🔗 多 Agent 图

- **交互可视化** - 查看 Agent 如何通信
- **瓶颈检测** - 发现性能瓶颈
- **社区检测** - 识别 Agent 集群
- **关键路径分析** - 找到最长依赖链

---

## 🚀 快速开始

### 前置条件

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) 包管理器
- Docker & Docker Compose（用于基础设施）

### 5 分钟快速上手

```bash
# 1. 克隆
git clone https://github.com/afine907/behavior-sense.git
cd behavior-sense

# 2. 安装依赖
uv sync

# 3. 启动基础设施（Pulsar、PostgreSQL、Redis 等）
docker compose -f infrastructure/docker/compose/base.yml up -d

# 4. 启动服务（在不同终端中）
uv run uvicorn behavior_mock.main:app --port 8001      # Agent 事件模拟器
uv run python -m behavior_stream                        # 流处理器
uv run uvicorn behavior_rules.main:app --port 8002     # 规则引擎
uv run uvicorn behavior_insight.main:app --port 8003   # Agent 洞察
uv run uvicorn behavior_audit.main:app --port 8004     # 审计工作流

# 5. 打开仪表板
cd apps/web && pnpm install && pnpm dev
# → http://localhost:5143
```

### 模拟 Agent 活动

```bash
# 启动正常多 Agent 场景
curl -X POST http://localhost:8001/api/mock/scenario/start \
  -H "Content-Type: application/json" \
  -d '{"scenario_type": "normal", "rate_per_second": 100}'

# 启动异常场景（成本飙升、注入尝试）
curl -X POST http://localhost:8001/api/mock/scenario/start \
  -H "Content-Type: application/json" \
  -d '{"scenario_type": "abnormal", "rate_per_second": 50}'
```

### 查询 Agent 洞察

```bash
# 获取 Agent 行为画像
curl http://localhost:8003/api/agents/agent-001

# 列出所有标记为成本异常的 Agent
curl http://localhost:8003/api/agents/tags?tag=cost_anomaly

# 获取 Agent 统计信息
curl http://localhost:8003/api/agents/agent-001/stats
```

---

## 📐 架构设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BehaviorSense 架构                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Mock       │    │   外部       │    │   SDK        │                  │
│  │   服务       │    │   Agent      │    │   客户端     │                  │
│  │   :8001      │    │   (LangChain │    │              │                  │
│  │              │    │    等)       │    │              │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                   │                           │
│         └───────────────────┼───────────────────┘                           │
│                             │                                               │
│                             ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Apache Pulsar :6650                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │  │
│  │  │   agent.    │  │   agent.    │  │   agent.    │                 │  │
│  │  │   events    │  │   alerts    │  │   aggreg.   │                 │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │  │
│  └─────────┼────────────────┼────────────────┼─────────────────────────┘  │
│            │                │                │                              │
│            ▼                ▼                ▼                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    流处理器                                          │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │  │
│  │  │   事件      │  │   12 个     │  │   窗口      │                 │  │
│  │  │   消费者    │──▶  检测器     │  │   聚合器    │                 │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │  │
│  │                                                                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │  │
│  │  │   异常      │  │   基线      │  │   模式      │                 │  │
│  │  │   评分器    │  │   构建器    │  │   检测器    │                 │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                             │                                               │
│         ┌───────────────────┼───────────────────┐                           │
│         │                   │                   │                           │
│         ▼                   ▼                   ▼                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   规则       │    │   洞察       │    │   审计       │                  │
│  │   服务       │    │   服务       │    │   服务       │                  │
│  │   :8002      │    │   :8003      │    │   :8004      │                  │
│  │              │    │              │    │              │                  │
│  │  - 规则 CRUD │    │  - 画像      │    │  - 订单      │                  │
│  │  - AST 评估  │    │  - 统计      │    │  - 工作流    │                  │
│  │  - 热重载    │    │  - 标签      │    │  - 审查      │                  │
│  │  - 动作      │    │  - 图        │    │  - 统计      │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│         │                   │                   │                           │
│         └───────────────────┼───────────────────┘                           │
│                             │                                               │
│                             ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         存储层                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │  │
│  │  │ PostgreSQL  │  │  ClickHouse │  │    Redis    │  │  Pulsar   │  │  │
│  │  │   :5432     │  │   :8123     │  │   :6379     │  │  :6650    │  │  │
│  │  │             │  │             │  │             │  │           │  │  │
│  │  │ - 画像      │  │ - 事件      │  │ - 标签      │  │ - 事件    │  │  │
│  │  │ - 规则      │  │ - 日志      │  │ - 缓存      │  │ - 告警    │  │  │
│  │  │ - 审计      │  │ - 追踪      │  │ - 限流      │  │ - 聚合    │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                             │                                               │
│                             ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                       前端 :5143                                     │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │  │
│  │  │ 仪表板   │ │  Agent  │ │  规则   │ │  审计   │ │  成本   │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| **运行时** | Python 3.11+ | 异步支持，类型提示 |
| **包管理器** | [uv](https://docs.astral.sh/uv/) | 比 pip 快 10 倍 |
| **Web 框架** | FastAPI | 异步，OpenAPI，类型安全 |
| **前端** | Next.js 14 | React，SSR，App Router |
| **流处理** | Pulsar Client | 实时事件处理 |
| **消息队列** | Apache Pulsar | 多租户，地理复制 |
| **数据库** | PostgreSQL | ACID，可靠 |
| **缓存** | Redis | 快速，发布/订阅支持 |
| **分析** | ClickHouse | OLAP 用于 Agent 行为分析 |
| **监控** | Prometheus + Grafana | 行业标准 |

---

## 📚 API 文档

### Agent Mock 服务 (`:8001`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/agent-mock/generate` | POST | 生成 Agent 事件 |
| `/api/agent-mock/scenario/start` | POST | 启动模拟场景 |
| `/api/agent-mock/scenarios` | GET | 列出场景 |
| `/ws/agent-events` | WebSocket | 实时事件流 |
| `/ws/alerts` | WebSocket | 实时告警流 |

### 规则引擎 (`:8002`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/rules` | GET/POST | 列出/创建规则 |
| `/api/rules/{id}` | GET/PUT/DELETE | 获取/更新/删除规则 |
| `/api/rules/evaluate` | POST | 评估规则 |
| `/api/rules/validate` | POST | 验证规则语法 |

### 洞察服务 (`:8003`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/agents` | GET | 列出 Agent |
| `/api/agents/{id}` | GET | 获取 Agent 画像 |
| `/api/agents/{id}/stats` | GET | 获取 Agent 统计 |
| `/api/agents/{id}/tags` | GET | 获取 Agent 标签 |
| `/api/agents/compare` | POST | 比较 Agent |
| `/api/agents/overview` | GET | 全局概览 |

### 审计服务 (`:8004`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/audit/order` | POST | 创建审计订单 |
| `/api/audit/orders` | GET | 列出订单 |
| `/api/audit/order/{id}/review` | PUT | 提交审查 |
| `/api/audit/stats` | GET | 审计统计 |

---

## 📁 项目结构

```
behavior-sense/
├── libs/
│   ├── core/                    # 共享库（模型、配置、安全）
│   │   └── src/behavior_core/
│   │       ├── models/          # Pydantic v2 数据模型
│   │       ├── config/          # pydantic-settings 配置
│   │       ├── security/        # JWT 认证，RBAC
│   │       ├── middleware/       # 限流，追踪
│   │       └── ...              # 指标，健康检查，弹性
│   ├── sdk/                     # Python SDK 客户端
│   │   └── src/behavior_sdk/
│   └── integrations/            # 框架集成
│       └── src/behavior_integrations/
│           ├── langchain/       # LangChain 回调
│           ├── llamaindex/      # LlamaIndex 回调
│           └── openai/          # OpenAI 包装器
│
├── packages/
│   ├── mock/                    # Agent 事件生成器 :8001
│   │   └── src/behavior_mock/
│   ├── stream/                  # 实时流处理器
│   │   └── src/behavior_stream/
│   │       ├── agent_detectors.py  # 12 个异常检测器
│   │       ├── agent_processor.py  # 事件处理器
│   │       └── operators/          # 窗口算子
│   ├── rules/                   # 规则引擎 :8002
│   │   └── src/behavior_rules/
│   ├── insight/                 # Agent 分析 :8003
│   │   └── src/behavior_insight/
│   ├── audit/                   # 审计工作流 :8004
│   │   └── src/behavior_audit/
│   └── logs/                    # 事件日志 :8005
│       └── src/behavior_logs/
│
├── apps/
│   └── web/                     # Next.js 前端 :5143
│       └── src/
│           ├── app/             # App Router 页面
│           └── components/      # React 组件
│
├── tests/                       # 测试套件
│   ├── test_core/               # 核心库测试
│   ├── test_stream/             # 流处理器测试
│   ├── test_api/                # API 端点测试
│   └── test_integration/        # 集成测试
│
├── infrastructure/
│   └── docker/                  # Docker 配置
│       ├── compose/             # Docker Compose 文件
│       └── *.sql                # 数据库模式
│
├── docs/                        # 文档
├── rules/                       # 示例 YAML 规则
├── examples/                    # SDK 使用示例
└── wiki/                        # 架构文档
```

---

## 🧪 测试

```bash
# 快速测试（无外部依赖）
uv run pytest tests/test_core/ tests/test_stream/ -v

# API 测试
uv run pytest tests/test_api/ -v

# 集成测试（需要 Docker）
docker compose -f infrastructure/docker/compose/test.yml up -d
TEST_REAL_DEPS=1 uv run pytest tests/ -v

# 带覆盖率
uv run pytest tests/ --cov=libs --cov=packages --cov-report=html
```

---

## 🤝 贡献指南

我们欢迎贡献！请参阅 [贡献指南](CONTRIBUTING.md)。

### 贡献者快速开始

```bash
# 1. Fork 并克隆
git clone https://github.com/YOUR_USERNAME/behavior-sense.git
cd behavior-sense

# 2. 安装依赖
uv sync

# 3. 创建功能分支
git checkout -b feat/your-feature

# 4. 修改并测试
uv run pytest tests/ -v

# 5. 提交 PR
git push origin feat/your-feature
```

### 提交规范

所有提交必须遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
feat(audit): 添加审计状态机用于审查工作流
fix(rules): 使用 AST 解析器防止 eval 注入
docs(api): 更新端点文档
```

---

## 📄 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE)。

---

## 🙏 致谢

- [Apache Pulsar](https://pulsar.apache.org/) - 多租户消息传递
- [ClickHouse](https://clickhouse.com/) - OLAP 分析
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [Next.js](https://nextjs.org/) - React 框架
- [Pydantic](https://docs.pydantic.dev/) - 数据验证

---

<p align="center">
  <b>如果觉得有用，请给个 Star ⭐！</b>
</p>
