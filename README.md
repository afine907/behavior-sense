<h1 align="center">
  <br>
  <a href="#"><img src="https://via.placeholder.com/200x200?text=BS" alt="BehaviorSense" width="120"></a>
  <br>
  BehaviorSense
  <br>
</h1>

<h4 align="center">🔍 Real-time AI Agent Behavior Analytics Platform</h4>

<p align="center">
  Monitor, analyze, and govern AI Agent behavior in real-time with 12 anomaly detectors.
</p>

<p align="center">
  <a href="#-why-behaviorsense">Why</a> •
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-api">API</a> •
  <a href="#-contributing">Contributing</a>
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

## 🎯 What is BehaviorSense?

**BehaviorSense** is an open-source, real-time AI Agent behavior analytics platform. It monitors, analyzes, and governs autonomous AI Agent systems with sub-second latency.

As teams deploy AI Agents that call tools, spend tokens, and interact with systems, visibility becomes critical. BehaviorSense provides:

- **🔍 Full Execution Tracing** - Track every agent action, tool call, and decision
- **🚨 12 Anomaly Detectors** - Catch cost spikes, prompt injection, dead loops, and more
- **📊 Multi-dimensional Scoring** - Quantify agent behavior risk
- **🛡️ Hot-reload Guardrails** - YAML-based rules, no restart needed
- **👥 Human-in-the-loop** - Built-in audit workflow for high-stakes decisions
- **🔗 Multi-Agent Graph** - Visualize agent interactions and dependencies

```
Agent Action → Stream Processing → Detection → Auto-tag / Flag for Audit
     ↓              < 1 second           ↓
  [Pulsar] ──────→ [Stream] ──────→ [Decision] ──────→ [Action]
```

---

## 💡 Why BehaviorSense?

| Pain Point | BehaviorSense Solution |
|------------|------------------------|
| **No visibility into agent tool calls** | Full execution tracing with latency and cost breakdowns |
| **Token costs spiral out of control** | Real-time cost anomaly detection with per-agent budgets |
| **Prompt injection goes undetected** | AST-based prompt analysis catches injection patterns instantly |
| **Multi-agent systems are opaque** | Correlation engine links actions across agent workflows |
| **Guardrails require code changes** | Hot-reload safety rules via YAML — no redeploy needed |
| **Hard to audit autonomous decisions** | Built-in human-in-the-loop review workflow |

### 🏆 Why Not Langfuse / Phoenix / LangSmith?

| Feature | BehaviorSense | Langfuse | Phoenix | LangSmith |
|---------|---------------|----------|---------|-----------|
| **Real-time Anomaly Detection** | ✅ 12 detectors | ❌ | 🔶 Basic | ❌ |
| **Rule Engine** | ✅ AST-safe, hot-reload | ❌ | ❌ | ❌ |
| **Cost Optimization** | ✅ Built-in suggestions | 🔶 Basic | 🔶 Basic | ✅ |
| **Multi-Agent Graph** | ✅ Dependency analysis | ❌ | ❌ | ❌ |
| **Behavior Replay** | ✅ Step-through | ❌ | ❌ | ❌ |
| **Compliance Checking** | ✅ 8 rules | ❌ | ❌ | ❌ |
| **Prompt Management** | ✅ Version control | ✅ | ❌ | ✅ |
| **OTel Integration** | ✅ Native | ✅ | ✅ | ❌ |
| **Framework Integrations** | ✅ LangChain, LlamaIndex, OpenAI | ✅ | ✅ | ✅ LangChain |
| **Self-hosted** | ✅ MIT License | ✅ MIT | 🔶 Elastic 2.0 | ❌ SaaS only |
| **License** | MIT | MIT | Elastic 2.0 | Proprietary |

---

## ✨ Features

### 🚨 12 Anomaly Detectors

| Detector | Detection Target | Threshold |
|----------|------------------|-----------|
| **AgentLoopDetector** | Dead loops | 5+ same actions in 60s |
| **CostSpikeDetector** | Cost spikes | >$10/min per agent |
| **TokenExplosionDetector** | Token explosion | >10K tokens in 10s |
| **ToolAbuseDetector** | Tool abuse | >50 calls/min |
| **TimeoutCascadeDetector** | Timeout cascades | 3+ timeouts in 5min |
| **CapabilityDriftDetector** | Capability drift | New tool usage patterns |
| **MultiAgentContentionDetector** | Resource contention | Coordinated resource access |
| **PromptInjectionDetector** | Prompt injection | Multiple injection indicators |
| **DataExfiltrationDetector** | Data leaks | Sensitive data in outputs |
| **HallucinationDetector** | Hallucinations | Low confidence + hedging |
| **CostExplosionDetector** | Fleet cost explosion | >$100/min fleet-wide |
| **AgentCollusionDetector** | Agent collusion | Excessive bilateral communication |

### 🛡️ Rule Engine

```yaml
# rules/agent_guardrails.yaml
- name: "High Token Cost Alert"
  condition: "token_cost > 5.00 and agent_role != 'planner'"
  priority: 10
  actions:
    - type: TAG_AGENT
      params: { tags: ["cost_anomaly"] }
    - type: TRIGGER_AUDIT
      params: { level: "high" }

- name: "Prompt Injection Detected"
  condition: "injection_score > 0.85"
  priority: 1
  actions:
    - type: BLOCK_EXECUTION
      params: { reason: "injection_detected" }
    - type: TRIGGER_AUDIT
      params: { level: "critical" }
```

**Hot-reload enabled** — modify guardrails without restart

### 📊 Agent Analytics

- **Agent Profiling** - Capabilities, history, risk assessment
- **Cost Tracking** - Per-agent and fleet-wide cost monitoring
- **Performance Metrics** - Latency, success rate, error rate
- **Behavior Patterns** - Loop detection, escalation, alternation
- **Optimization Suggestions** - Cost, performance, tool usage
- **Compliance Checking** - Safety, cost, tool, privacy policies

### 🔗 Multi-Agent Graph

- **Interaction Visualization** - See how agents communicate
- **Bottleneck Detection** - Find performance bottlenecks
- **Community Detection** - Identify agent clusters
- **Critical Path Analysis** - Find the longest dependency chain

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker & Docker Compose (for infrastructure)

### 5-Minute Setup

```bash
# 1. Clone
git clone https://github.com/afine907/behavior-sense.git
cd behavior-sense

# 2. Install dependencies
uv sync

# 3. Start infrastructure (Pulsar, PostgreSQL, Redis, etc.)
docker compose -f infrastructure/docker/compose/base.yml up -d

# 4. Start services (in separate terminals)
uv run uvicorn behavior_mock.main:app --port 8001      # Agent event simulator
uv run python -m behavior_stream                        # Stream processor
uv run uvicorn behavior_rules.main:app --port 8002     # Rule engine
uv run uvicorn behavior_insight.main:app --port 8003   # Agent insights
uv run uvicorn behavior_audit.main:app --port 8004     # Audit workflow

# 5. Open dashboard
cd apps/web && pnpm install && pnpm dev
# → http://localhost:5143
```

### Simulate Agent Activity

```bash
# Start a normal multi-agent scenario
curl -X POST http://localhost:8001/api/mock/scenario/start \
  -H "Content-Type: application/json" \
  -d '{"scenario_type": "normal", "rate_per_second": 100}'

# Start an anomaly scenario (cost spike, injection attempts)
curl -X POST http://localhost:8001/api/mock/scenario/start \
  -H "Content-Type: application/json" \
  -d '{"scenario_type": "abnormal", "rate_per_second": 50}'
```

### Query Agent Insights

```bash
# Get an agent's behavior profile
curl http://localhost:8003/api/agents/agent-001

# List all agents flagged with cost anomalies
curl http://localhost:8003/api/agents/tags?tag=cost_anomaly

# Get agent statistics
curl http://localhost:8003/api/agents/agent-001/stats
```

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BehaviorSense Architecture                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Mock       │    │   External   │    │   SDK        │                  │
│  │   Service    │    │   Agents     │    │   Client     │                  │
│  │   :8001      │    │   (LangChain │    │              │                  │
│  │              │    │    etc.)      │    │              │                  │
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
│  │                    Stream Processor                                  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │  │
│  │  │   Event     │  │   12        │  │   Window    │                 │  │
│  │  │   Consumer  │──▶  Detectors  │  │   Aggregator│                 │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │  │
│  │                                                                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │  │
│  │  │   Anomaly   │  │   Baseline  │  │   Pattern   │                 │  │
│  │  │   Scorer    │  │   Builder   │  │   Detector  │                 │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                             │                                               │
│         ┌───────────────────┼───────────────────┐                           │
│         │                   │                   │                           │
│         ▼                   ▼                   ▼                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Rules      │    │   Insight    │    │   Audit      │                  │
│  │   Service    │    │   Service    │    │   Service    │                  │
│  │   :8002      │    │   :8003      │    │   :8004      │                  │
│  │              │    │              │    │              │                  │
│  │  - Rule CRUD │    │  - Profiles  │    │  - Orders    │                  │
│  │  - AST Eval  │    │  - Stats     │    │  - Workflow  │                  │
│  │  - Hot-reload│    │  - Tags      │    │  - Review    │                  │
│  │  - Actions   │    │  - Graph     │    │  - Stats     │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│         │                   │                   │                           │
│         └───────────────────┼───────────────────┘                           │
│                             │                                               │
│                             ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Storage Layer                                │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │  │
│  │  │ PostgreSQL  │  │  ClickHouse │  │    Redis    │  │  Pulsar   │  │  │
│  │  │   :5432     │  │   :8123     │  │   :6379     │  │  :6650    │  │  │
│  │  │             │  │             │  │             │  │           │  │  │
│  │  │ - Profiles  │  │ - Events    │  │ - Tags      │  │ - Events  │  │  │
│  │  │ - Rules     │  │ - Logs      │  │ - Cache     │  │ - Alerts  │  │  │
│  │  │ - Audit     │  │ - Traces    │  │ - Rate Limit│  │ - Agg     │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                             │                                               │
│                             ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                       Frontend :5143                                 │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │  │
│  │  │Dashboard │ │  Agents  │ │  Rules   │ │  Audit   │ │  Costs   │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Runtime** | Python 3.11+ | Async support, type hints |
| **Package Manager** | [uv](https://docs.astral.sh/uv/) | 10x faster than pip |
| **Web Framework** | FastAPI | Async, OpenAPI, type-safe |
| **Frontend** | Next.js 14 | React, SSR, App Router |
| **Stream Processing** | Pulsar Client | Real-time event processing |
| **Message Queue** | Apache Pulsar | Multi-tenancy, geo-replication |
| **Database** | PostgreSQL | ACID, reliable |
| **Cache** | Redis | Fast, pub/sub support |
| **Analytics** | ClickHouse | OLAP for agent behavior analysis |
| **Monitoring** | Prometheus + Grafana | Industry standard |

---

## 📚 API Reference

### Agent Mock Service (`:8001`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agent-mock/generate` | POST | Generate agent events |
| `/api/agent-mock/scenario/start` | POST | Start simulation scenario |
| `/api/agent-mock/scenarios` | GET | List scenarios |
| `/ws/agent-events` | WebSocket | Real-time event stream |
| `/ws/alerts` | WebSocket | Real-time alert stream |

### Rule Engine (`:8002`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/rules` | GET/POST | List/Create rules |
| `/api/rules/{id}` | GET/PUT/DELETE | Get/Update/Delete rule |
| `/api/rules/evaluate` | POST | Evaluate rules |
| `/api/rules/validate` | POST | Validate rule syntax |

### Insight Service (`:8003`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agents` | GET | List agents |
| `/api/agents/{id}` | GET | Get agent profile |
| `/api/agents/{id}/stats` | GET | Get agent statistics |
| `/api/agents/{id}/tags` | GET | Get agent tags |
| `/api/agents/compare` | POST | Compare agents |
| `/api/agents/overview` | GET | Global overview |

### Audit Service (`:8004`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/audit/order` | POST | Create audit order |
| `/api/audit/orders` | GET | List orders |
| `/api/audit/order/{id}/review` | PUT | Submit review |
| `/api/audit/stats` | GET | Audit statistics |

---

## 📁 Project Structure

```
behavior-sense/
├── libs/
│   ├── core/                    # Shared library (models, config, security)
│   │   └── src/behavior_core/
│   │       ├── models/          # Pydantic v2 data models
│   │       ├── config/          # Settings with pydantic-settings
│   │       ├── security/        # JWT auth, RBAC
│   │       ├── middleware/       # Rate limiting, tracing
│   │       └── ...              # Metrics, health, resilience
│   ├── sdk/                     # Python SDK client
│   │   └── src/behavior_sdk/
│   └── integrations/            # Framework integrations
│       └── src/behavior_integrations/
│           ├── langchain/       # LangChain callback
│           ├── llamaindex/      # LlamaIndex callback
│           └── openai/          # OpenAI wrapper
│
├── packages/
│   ├── mock/                    # Agent event generator :8001
│   │   └── src/behavior_mock/
│   ├── stream/                  # Real-time stream processor
│   │   └── src/behavior_stream/
│   │       ├── agent_detectors.py  # 12 anomaly detectors
│   │       ├── agent_processor.py  # Event processor
│   │       └── operators/          # Window operators
│   ├── rules/                   # Rule engine :8002
│   │   └── src/behavior_rules/
│   ├── insight/                 # Agent analytics :8003
│   │   └── src/behavior_insight/
│   ├── audit/                   # Audit workflow :8004
│   │   └── src/behavior_audit/
│   └── logs/                    # Event logs :8005
│       └── src/behavior_logs/
│
├── apps/
│   └── web/                     # Next.js frontend :5143
│       └── src/
│           ├── app/             # App Router pages
│           └── components/      # React components
│
├── tests/                       # Test suite
│   ├── test_core/               # Core library tests
│   ├── test_stream/             # Stream processor tests
│   ├── test_api/                # API endpoint tests
│   └── test_integration/        # Integration tests
│
├── infrastructure/
│   └── docker/                  # Docker configuration
│       ├── compose/             # Docker Compose files
│       └── *.sql                # Database schemas
│
├── docs/                        # Documentation
├── rules/                       # Sample YAML rules
├── examples/                    # SDK usage examples
└── wiki/                        # Architecture docs
```

---

## 🧪 Testing

```bash
# Fast tests (no external dependencies)
uv run pytest tests/test_core/ tests/test_stream/ -v

# API tests
uv run pytest tests/test_api/ -v

# Integration tests (requires Docker)
docker compose -f infrastructure/docker/compose/test.yml up -d
TEST_REAL_DEPS=1 uv run pytest tests/ -v

# With coverage
uv run pytest tests/ --cov=libs --cov=packages --cov-report=html
```

---

## 🤝 Contributing

We welcome contributions! See [Contributing Guidelines](CONTRIBUTING.md).

### Quick Start for Contributors

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/behavior-sense.git
cd behavior-sense

# 2. Install dependencies
uv sync

# 3. Create feature branch
git checkout -b feat/your-feature

# 4. Make changes and test
uv run pytest tests/ -v

# 5. Submit PR
git push origin feat/your-feature
```

### Commit Convention

All commits must follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(audit): add audit state machine for review workflow
fix(rules): prevent eval injection with AST parser
docs(api): update endpoint documentation
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [Apache Pulsar](https://pulsar.apache.org/) - Multi-tenant messaging
- [ClickHouse](https://clickhouse.com/) - OLAP analytics
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Next.js](https://nextjs.org/) - React framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation

---

<p align="center">
  <b>Star ⭐ this repo if you find it useful!</b>
</p>
