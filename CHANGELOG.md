# Changelog

All notable changes to BehaviorSense will be documented in this file.

## [2.0.0-alpha] - 2024-01-20

### 🎉 Major Release: AI Agent Behavior Analytics

BehaviorSense has been transformed from a user behavior analytics engine into a **real-time AI Agent behavior monitoring and analytics platform**.

### ✨ Added

#### Core Agent Models
- `AgentBehavior` - Agent event model with trace context, token usage, tool calls
- `TokenUsage` - LLM token consumption tracking with cost estimation
- `ToolCall` - Tool invocation tracking with 10+ tool types
- `AgentSession` - Task/mission tracking with delegation chains
- `AgentTrace` - OpenTelemetry-style execution trace (DAG)
- `AgentCapability` - Agent skill profiling with auto-level progression
- `AgentAggregation` - Agent metrics aggregation (tokens, cost, performance)
- `AgentAlert` - 20+ agent-specific alert types
- `AgentProfile` - Agent profiling with safety ratings and cost tiers
- `AgentStat` - Time-windowed agent statistics

#### Anomaly Detection
- `AgentLoopDetector` - Dead loop detection (repetitive behavior)
- `CostSpikeDetector` - Token cost anomaly detection
- `TokenExplosionDetector` - Excessive token usage detection
- `ToolAbuseDetector` - Tool call frequency anomaly detection
- `TimeoutCascadeDetector` - Cascading timeout detection
- `CapabilityDriftDetector` - Behavior deviation from baseline
- `MultiAgentContentionDetector` - Resource competition detection
- `AgentAnomalyScorer` - Multi-dimensional anomaly scoring (0-100)

#### Rules Engine
- 22 preset agent monitoring rules in 6 categories:
  - Cost control (budget, spike, token explosion)
  - Security (injection, unauthorized tool, data exfiltration)
  - Performance (latency SLA, timeout cascade, error rate)
  - Anomaly (dead loop, oscillation, infinite retry)
  - Multi-agent (delegation depth, resource contention, cascading failure)
  - Compliance (audit trail, PII access, model compliance)

#### Agent Insight API
- Agent CRUD operations (create, read, update, delete)
- Agent tag management (get, set, delete, query by value)
- Agent statistics (events, tokens, cost, performance)
- Agent comparison across metrics
- Agent risk assessment
- Global agent overview

#### Agent Trace API
- Trace listing with filtering
- Full trace retrieval with spans
- Waterfall visualization data
- Timeline events
- Error analysis
- Critical path calculation

#### Advanced Analytics
- `AgentGraphAnalyzer` - Dependency graph with cycle detection
- `BehaviorReplay` - Step-through replay of agent execution traces
- `NotificationService` - Alert dispatch (webhook, Slack, console)
- `OptimizationEngine` - Cost/performance/safety suggestions
- `ComplianceChecker` - 8 compliance rules (PII, budget, models, tools, audit)
- `BaselineBuilder` - Agent behavior baseline construction
- `PatternDetector` - Loop/alternation/escalation pattern detection

#### Mock & Simulation
- `AgentEventGenerator` - Realistic agent event generation
- 4 simulation scenarios: normal, loop, cost_explosion, cascading_failure
- WebSocket real-time event streaming
- WebSocket real-time alert streaming

#### Frontend Dashboard
- Real-time monitoring overview
- Agent list with search/filter/sort
- Agent detail with 5 tabs (overview, timeline, costs, tools, traces)
- Trace list with waterfall visualization
- Alert center with severity filtering
- Rules management page
- Cost analysis dashboard
- Audit workbench
- Settings page (notifications, budgets, rules, API keys)

#### Infrastructure
- ClickHouse schema for agent events (6 tables + 2 materialized views)
- Docker Compose for full agent analytics stack
- Comprehensive deployment guide
- Complete API reference documentation

#### Testing
- Unit tests for all agent models (50+ test functions)
- Unit tests for all anomaly detectors (20+ test functions)
- Unit tests for optimization engine
- Unit tests for compliance checker
- Unit tests for pattern detector
- API integration tests
- E2E integration tests

### 🔄 Changed
- README.md updated with AI Agent Analytics positioning
- CLAUDE.md updated with new architecture
- Project pivoted from user behavior to agent behavior analysis

### 📦 Infrastructure
- Added ClickHouse agent schema (init_agent.sql)
- Added Docker Compose agent configuration (docker-compose.agent.yml)

## [1.0.0] - 2024-01-15

### Initial Release
- User behavior event processing
- Real-time stream processing with Pulsar
- Rule engine with AST-based safe evaluation
- User profiling and tagging
- Audit workflow
- Event log retrieval
