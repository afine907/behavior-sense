# BehaviorSense 架构设计

## 系统概览

BehaviorSense 是一个实时 AI Agent 行为分析平台，由以下核心组件组成：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BehaviorSense 架构                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        数据接入层                                    │  │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │  │
│  │  │   Mock       │    │   External   │    │   SDK        │           │  │
│  │  │   Service    │    │   Agents     │    │   Client     │           │  │
│  │  │   :8001      │    │   (LangChain │    │              │           │  │
│  │  │              │    │    etc.)      │    │              │           │  │
│  │  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘           │  │
│  │         └───────────────────┼───────────────────┘                   │  │
│  └─────────────────────────────┼───────────────────────────────────────┘  │
│                                │                                           │
│                                ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      消息队列层                                      │  │
│  │                      Apache Pulsar :6650                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │  │
│  │  │   agent.    │  │   agent.    │  │   agent.    │                 │  │
│  │  │   events    │  │   alerts    │  │   aggreg.   │                 │  │
│  │  │   Topic     │  │   Topic     │  │   Topic     │                 │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │  │
│  └─────────┼────────────────┼────────────────┼─────────────────────────┘  │
│            │                │                │                              │
│            ▼                ▼                ▼                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        流处理层                                      │  │
│  │                        Stream Processor                              │  │
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
│                                │                                           │
│         ┌──────────────────────┼──────────────────────┐                    │
│         │                      │                      │                    │
│         ▼                      ▼                      ▼                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│  │   Rules      │    │   Insight    │    │   Audit      │                 │
│  │   Service    │    │   Service    │    │   Service    │                 │
│  │   :8002      │    │   :8003      │    │   :8004      │                 │
│  │              │    │              │    │              │                 │
│  │  ┌────────┐  │    │  ┌────────┐  │    │  ┌────────┐  │                 │
│  │  │Rule    │  │    │  │Profile │  │    │  │Order   │  │                 │
│  │  │CRUD    │  │    │  │Manager │  │    │  │Manager │  │                 │
│  │  └────────┘  │    │  └────────┘  │    │  └────────┘  │                 │
│  │  ┌────────┐  │    │  ┌────────┐  │    │  ┌────────┐  │                 │
│  │  │AST     │  │    │  │Stats   │  │    │  │Review  │  │                 │
│  │  │Engine  │  │    │  │Tracker │  │    │  │Workflow│  │                 │
│  │  └────────┘  │    │  └────────┘  │    │  └────────┘  │                 │
│  │  ┌────────┐  │    │  ┌────────┐  │    │  ┌────────┐  │                 │
│  │  │Hot     │  │    │  │Tag     │  │    │  │Audit   │  │                 │
│  │  │Reload  │  │    │  │Service │  │    │  │Stats   │  │                 │
│  │  └────────┘  │    │  └────────┘  │    │  └────────┘  │                 │
│  │  ┌────────┐  │    │  ┌────────┐  │    │              │                 │
│  │  │Action  │  │    │  │Graph   │  │    │              │                 │
│  │  │Handler │  │    │  │Analyzer│  │    │              │                 │
│  │  └────────┘  │    │  └────────┘  │    │              │                 │
│  └──────────────┘    └──────────────┘    └──────────────┘                 │
│         │                      │                      │                    │
│         └──────────────────────┼──────────────────────┘                    │
│                                │                                           │
│                                ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        存储层                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │  │
│  │  │ PostgreSQL  │  │  ClickHouse │  │    Redis    │  │  Pulsar   │  │  │
│  │  │   :5432     │  │   :8123     │  │   :6379     │  │  :6650    │  │  │
│  │  │             │  │             │  │             │  │           │  │  │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌───────┐│  │  │
│  │  │ │Profiles │ │  │ │Events   │ │  │ │Tags     │ │  │ │Events ││  │  │
│  │  │ │Rules    │ │  │ │Logs     │ │  │ │Cache    │ │  │ │Alerts ││  │  │
│  │  │ │Audit    │ │  │ │Traces   │ │  │ │RateLimit│ │  │ │Agg    ││  │  │
│  │  │ │Orders   │ │  │ │Stats    │ │  │ │Sessions │ │  │ │       ││  │  │
│  │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │  │ └───────┘│  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                │                                           │
│                                ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        前端层                                        │  │
│  │                        Next.js :5143                                 │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │  │
│  │  │Dashboard │ │  Agents  │ │  Rules   │ │  Audit   │ │  Costs   │  │  │
│  │  │ 仪表板   │ │  Agent   │ │  规则    │ │  审计    │ │  成本    │  │  │
│  │  │          │ │  管理    │ │  管理    │ │  中心    │ │  分析    │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐               │  │
│  │  │  Traces  │ │  Alerts  │ │  Logs    │ │ Settings │               │  │
│  │  │  追踪    │ │  告警    │ │  日志    │ │  设置    │               │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 组件详解

### 1. 数据接入层

#### Mock Service (:8001)
- **功能**: 生成模拟 AI Agent 事件
- **Agent 配置**: 5 种预配置 Agent（Researcher, Coder, Analyst, Orchestrator, Assistant）
- **场景模拟**: 4 种场景（Normal, Loop, Cost Explosion, Cascading Failure）
- **WebSocket**: 实时事件流和告警流

#### SDK Client
- **功能**: Python 异步客户端
- **特性**: 支持所有 API 端点，上下文管理器

#### 框架集成
- **LangChain**: 回调函数集成
- **LlamaIndex**: 回调函数集成
- **OpenAI**: 包装器集成

### 2. 消息队列层

#### Apache Pulsar (:6650)
- **agent.events**: Agent 事件主题
- **agent.alerts**: 异常告警主题
- **agent.aggregation**: 聚合统计主题

### 3. 流处理层

#### Stream Processor
- **Event Consumer**: 事件消费者
- **12 Detectors**: 异常检测器
- **Window Aggregator**: 窗口聚合器
- **Anomaly Scorer**: 异常评分器
- **Baseline Builder**: 基线构建器
- **Pattern Detector**: 模式检测器

#### 12 个异常检测器

| 检测器 | 检测目标 | 阈值 |
|--------|----------|------|
| AgentLoopDetector | 死循环 | 60 秒内 5+ 次相同操作 |
| CostSpikeDetector | 成本飙升 | 每 Agent >$10/分钟 |
| TokenExplosionDetector | Token 爆炸 | 10 秒内 >10K Token |
| ToolAbuseDetector | 工具滥用 | >50 次调用/分钟 |
| TimeoutCascadeDetector | 超时级联 | 5 分钟内 3+ 次超时 |
| CapabilityDriftDetector | 能力漂移 | 新工具使用模式 |
| MultiAgentContentionDetector | 资源争用 | 协调资源访问 |
| PromptInjectionDetector | Prompt 注入 | 多个注入指标 |
| DataExfiltrationDetector | 数据泄露 | 输出中的敏感数据 |
| HallucinationDetector | 幻觉 | 低置信度 + 模糊语言 |
| CostExplosionDetector | 舰队成本爆炸 | 舰队整体 >$100/分钟 |
| AgentCollusionDetector | Agent 串通 | 过度双边通信 |

### 4. 业务服务层

#### Rules Service (:8002)
- **Rule CRUD**: 规则管理 API
- **AST Engine**: AST 安全评估引擎
- **Hot Reload**: YAML/DB 热重载
- **Action Handler**: 动作处理器（TAG_AGENT, BLOCK_EXECUTION, TRIGGER_AUDIT）

#### Insight Service (:8003)
- **Profile Manager**: Agent 画像管理
- **Stats Tracker**: 统计跟踪
- **Tag Service**: 标签服务
- **Graph Analyzer**: 关系图分析
- **Optimization Engine**: 优化建议引擎
- **Compliance Checker**: 合规检查器

#### Audit Service (:8004)
- **Order Manager**: 审计订单管理
- **Review Workflow**: 审查工作流
- **Audit Stats**: 审计统计

### 5. 存储层

#### PostgreSQL (:5432)
- **agent_profiles**: Agent 画像表
- **agent_stats**: Agent 统计表
- **agent_tags**: Agent 标签表
- **rules**: 规则表
- **audit_orders**: 审计订单表

#### ClickHouse (:8123)
- **agent_event_logs**: Agent 事件日志（高吞吐量追加写入）
- **agent_token_usage_mv**: Token 使用物化视图
- **agent_tool_usage_mv**: 工具使用物化视图
- **agent_alerts**: Agent 告警日志
- **agent_sessions**: Agent 会话摘要
- **agent_daily_stats**: Agent 每日统计

#### Redis (:6379)
- **agent:tags:{agent_id}**: Agent 标签哈希
- **tags:index:{tag_name}**: 标签索引集合
- **rate_limit:{client_ip}**: 限流滑动窗口
- **tag:updates**: 标签更新发布/订阅
- **tag:deletes**: 标签删除发布/订阅

### 6. 前端层

#### Next.js (:5143)
- **Dashboard**: 仪表板，实时监控
- **Agents**: Agent 管理
- **Rules**: 规则管理
- **Audit**: 审计中心
- **Costs**: 成本分析
- **Traces**: 执行追踪
- **Alerts**: 告警管理
- **Logs**: 日志查询
- **Settings**: 系统设置

## 数据流

### 1. 事件采集流

```
Agent Action → SDK/Mock → Pulsar (agent.events) → Stream Consumer
```

### 2. 检测处理流

```
Stream Consumer → 12 Detectors → Anomaly Scorer → Pulsar (agent.alerts)
```

### 3. 聚合统计流

```
Stream Consumer → Window Aggregator → Pulsar (agent.aggregation)
```

### 4. 规则评估流

```
Pulsar (agent.alerts) → Rules Service → AST Engine → Action Handler
```

### 5. 画像更新流

```
Action Handler → Insight Service → PostgreSQL + Redis
```

### 6. 审计工作流

```
Action Handler → Audit Service → PostgreSQL → Review Workflow
```

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| **运行时** | Python 3.11+ | 异步支持，类型提示 |
| **包管理器** | uv | 比 pip 快 10 倍 |
| **Web 框架** | FastAPI | 异步，OpenAPI，类型安全 |
| **前端** | Next.js 14 | React，SSR，App Router |
| **流处理** | Pulsar Client | 实时事件处理 |
| **消息队列** | Apache Pulsar | 多租户，地理复制 |
| **数据库** | PostgreSQL | ACID，可靠 |
| **缓存** | Redis | 快速，发布/订阅支持 |
| **分析** | ClickHouse | OLAP 用于 Agent 行为分析 |
| **监控** | Prometheus + Grafana | 行业标准 |

## 部署架构

### 开发环境

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │PostgreSQL│ │ClickHouse│ │  Redis  │ │ Pulsar  │      │
│  │  :5432   │ │  :8123   │ │  :6379  │ │  :6650  │      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
└─────────────────────────────────────────────────────────┘
```

### 生产环境

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │                 Ingress Controller               │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │ Rules   │ │ Insight │ │  Audit  │ │  Mock   │      │
│  │ Service │ │ Service │ │ Service │ │ Service │      │
│  │ x3      │ │ x3      │ │ x2      │ │ x1      │      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Stream Processor x3                 │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │PostgreSQL│ │ClickHouse│ │  Redis  │ │ Pulsar  │      │
│  │ Cluster │ │ Cluster │ │ Cluster │ │ Cluster │      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
└─────────────────────────────────────────────────────────┘
```

## 扩展性

### 水平扩展

- **Pulsar**: 增加分区数
- **FastAPI**: 增加实例数
- **PostgreSQL**: 读写分离
- **Redis**: 集群模式
- **ClickHouse**: 分片集群

### 垂直扩展

- **Stream Processor**: 增加 worker 数
- **数据库**: 增加内存和 CPU
- **缓存**: 增加内存

## 容错设计

### 消息队列

- Pulsar 持久化存储
- 消息确认机制
- 死信队列处理

### 数据库

- PostgreSQL 主从复制
- ClickHouse 副本集
- Redis Sentinel

### 服务

- 电路断路器
- 重试机制
- 超时控制
- 优雅降级

## 监控指标

### 业务指标

- 事件处理延迟
- 检测准确率
- 告警数量
- 成本统计

### 系统指标

- CPU/内存使用率
- 磁盘 I/O
- 网络流量
- 队列积压

### Prometheus 指标

```python
# 事件处理
agent_events_processed_total
agent_events_failed_total

# 检测
agent_alerts_generated_total
agent_detection_latency_seconds

# 成本
agent_cost_tracked_usd
agent_tokens_processed_total

# 系统
agent_active_count
agent_processing_latency_seconds
```
