"""
AI Agent 模型单元测试

覆盖所有 Agent 相关模型：AgentBehavior, TokenUsage, ToolCall, AgentSession,
AgentTrace, AgentCapability, AgentAggregation, AgentAlert, AgentProfile, AgentStat.
"""
import uuid
from datetime import UTC, datetime, timedelta

import pytest

# -- agent_event models --
from behavior_core.models.agent_event import (
    AgentBehavior,
    AgentEventType,
    AgentType,
    StandardAgentEvent,
)

# -- token_usage model (standalone module) --
from behavior_core.models.token_usage import TokenUsage

# -- tool_call model (standalone module) --
from behavior_core.models.tool_call import ToolCall, ToolType

# -- agent_session model --
from behavior_core.models.agent_session import (
    AgentSession,
    TaskPriority,
    TaskStatus,
)

# -- agent_trace model --
from behavior_core.models.agent_trace import (
    AgentTrace,
    SpanKind,
    SpanStatus,
    TraceSpan,
)

# -- agent_capability model --
from behavior_core.models.agent_capability import (
    AgentCapability,
    AgentCapabilityMap,
    CapabilityCategory,
    CapabilityLevel,
)

# -- agent_aggregation model --
from behavior_core.models.agent_aggregation import (
    AgentAggregation,
    CostBreakdown,
    PerformanceMetrics,
)

# -- agent_alert model --
from behavior_core.models.agent_alert import (
    AgentAlert,
    AgentAlertType,
    AlertRule,
    AlertSeverity,
    AutoAction,
)

# -- agent_profile model --
from behavior_core.models.agent_profile import (
    AgentComparison,
    AgentProfile,
    AgentStat,
    AgentStatus,
    CostTier,
    SafetyRating,
)


# ============================================================
# 1. AgentEventType / AgentType enum tests
# ============================================================

class TestAgentEventType:
    """Agent 事件类型枚举测试"""

    def test_event_type_values(self):
        assert AgentEventType.TOOL_CALL == "tool_call"
        assert AgentEventType.TOOL_RESULT == "tool_result"
        assert AgentEventType.LLM_REQUEST == "llm_request"
        assert AgentEventType.LLM_RESPONSE == "llm_response"
        assert AgentEventType.MEMORY_READ == "memory_read"
        assert AgentEventType.MEMORY_WRITE == "memory_write"
        assert AgentEventType.PLAN_CREATE == "plan_create"
        assert AgentEventType.PLAN_UPDATE == "plan_update"
        assert AgentEventType.DELEGATION == "delegation"
        assert AgentEventType.ERROR == "error"
        assert AgentEventType.RETRY == "retry"
        assert AgentEventType.TIMEOUT == "timeout"
        assert AgentEventType.GUARDRAIL_TRIGGER == "guardrail_trigger"
        assert AgentEventType.COST_ALERT == "cost_alert"
        assert AgentEventType.SESSION_START == "session_start"
        assert AgentEventType.SESSION_END == "session_end"

    def test_event_type_is_string_enum(self):
        assert isinstance(AgentEventType.TOOL_CALL.value, str)

    def test_event_type_count(self):
        assert len(AgentEventType) == 16


class TestAgentType:
    """Agent 类型枚举测试"""

    def test_agent_type_values(self):
        assert AgentType.LLM_AGENT == "llm_agent"
        assert AgentType.TOOL_AGENT == "tool_agent"
        assert AgentType.WORKFLOW_AGENT == "workflow_agent"
        assert AgentType.MULTI_AGENT == "multi_agent"
        assert AgentType.AUTONOMOUS == "autonomous"
        assert AgentType.HUMAN_IN_LOOP == "human_in_loop"

    def test_agent_type_count(self):
        assert len(AgentType) == 6


# ============================================================
# 2. AgentBehavior model tests
# ============================================================

class TestAgentBehavior:
    """Agent 行为事件模型测试"""

    def test_create_agent_behavior(self):
        event = AgentBehavior(
            agent_id="agent_001",
            agent_type=AgentType.LLM_AGENT,
            event_type=AgentEventType.LLM_REQUEST,
        )
        assert event.agent_id == "agent_001"
        assert event.agent_type == AgentType.LLM_AGENT.value
        assert event.event_type == AgentEventType.LLM_REQUEST.value
        assert event.event_id is not None
        assert event.timestamp is not None

    def test_agent_behavior_default_values(self):
        event = AgentBehavior(
            agent_id="agent_001",
            agent_type=AgentType.TOOL_AGENT,
            event_type=AgentEventType.TOOL_CALL,
        )
        assert event.trace_id is None
        assert event.parent_span_id is None
        assert event.session_id is None
        assert event.task_id is None
        assert event.model_name is None
        assert event.model_version is None
        assert event.properties == {}
        assert event.token_usage is None
        assert event.tool_call is None
        assert event.latency_ms is None
        assert event.success is None
        assert event.error_type is None
        assert event.error_message is None
        assert event.cost_usd is None

    def test_agent_behavior_with_all_fields(self):
        event = AgentBehavior(
            agent_id="agent_001",
            agent_type=AgentType.LLM_AGENT,
            event_type=AgentEventType.LLM_RESPONSE,
            trace_id="trace_abc",
            parent_span_id="span_123",
            session_id="sess_001",
            task_id="task_001",
            model_name="gpt-4",
            model_version="2024-06",
            properties={"temperature": 0.7},
            latency_ms=250.5,
            success=True,
            cost_usd=0.0035,
        )
        assert event.trace_id == "trace_abc"
        assert event.parent_span_id == "span_123"
        assert event.session_id == "sess_001"
        assert event.task_id == "task_001"
        assert event.model_name == "gpt-4"
        assert event.properties["temperature"] == 0.7
        assert event.latency_ms == 250.5
        assert event.success is True
        assert event.cost_usd == 0.0035

    def test_agent_behavior_with_error(self):
        event = AgentBehavior(
            agent_id="agent_001",
            agent_type=AgentType.LLM_AGENT,
            event_type=AgentEventType.ERROR,
            success=False,
            error_type="RateLimitError",
            error_message="Rate limit exceeded",
        )
        assert event.success is False
        assert event.error_type == "RateLimitError"
        assert event.error_message == "Rate limit exceeded"

    def test_agent_behavior_json_serialization(self):
        event = AgentBehavior(
            agent_id="agent_001",
            agent_type=AgentType.AUTONOMOUS,
            event_type=AgentEventType.SESSION_START,
        )
        data = event.model_dump()
        assert "event_id" in data
        assert "agent_id" in data
        assert "timestamp" in data
        assert data["agent_id"] == "agent_001"

    def test_agent_behavior_unique_event_ids(self):
        e1 = AgentBehavior(
            agent_id="a1",
            agent_type=AgentType.LLM_AGENT,
            event_type=AgentEventType.LLM_REQUEST,
        )
        e2 = AgentBehavior(
            agent_id="a1",
            agent_type=AgentType.LLM_AGENT,
            event_type=AgentEventType.LLM_REQUEST,
        )
        assert e1.event_id != e2.event_id

    def test_agent_behavior_with_embedded_tool_call(self):
        # AgentBehavior.tool_call references the ToolCall defined in agent_event.py
        from behavior_core.models.agent_event import ToolCall as AgentToolCall

        tool = AgentToolCall(
            tool_name="search_web",
            tool_input={"query": "test"},
        )
        event = AgentBehavior(
            agent_id="agent_001",
            agent_type=AgentType.TOOL_AGENT,
            event_type=AgentEventType.TOOL_CALL,
            tool_call=tool,
        )
        assert event.tool_call is not None
        assert event.tool_call.tool_name == "search_web"


# ============================================================
# 3. StandardAgentEvent model tests
# ============================================================

class TestStandardAgentEvent:
    """标准化 Agent 事件模型测试"""

    def test_create_standard_agent_event(self):
        event = StandardAgentEvent(
            event_id="evt_001",
            agent_id="agent_001",
            agent_type="llm_agent",
            event_type="llm_request",
            timestamp=datetime.now(UTC),
        )
        assert event.event_id == "evt_001"
        assert event.tags == []
        assert event.properties == {}
        assert event.agent_context == {}
        assert event.cost_context == {}
        assert event.safety_context == {}

    def test_standard_agent_event_with_contexts(self):
        event = StandardAgentEvent(
            event_id="evt_002",
            agent_id="agent_001",
            agent_type="tool_agent",
            event_type="tool_call",
            timestamp=datetime.now(UTC),
            tags=["high_cost", "slow"],
            agent_context={"model": "gpt-4", "version": "0613"},
            cost_context={"total_tokens": 1500, "cost_usd": 0.045},
            safety_context={"guardrail_triggered": False},
        )
        assert len(event.tags) == 2
        assert event.agent_context["model"] == "gpt-4"
        assert event.cost_context["cost_usd"] == 0.045


# ============================================================
# 4. TokenUsage model tests (from token_usage.py)
# ============================================================

class TestTokenUsage:
    """Token 消耗模型测试"""

    def test_create_token_usage_defaults(self):
        usage = TokenUsage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0
        assert usage.cached_tokens == 0
        assert usage.cost_usd == 0.0
        assert usage.cache_hit_ratio == 0.0

    def test_token_usage_auto_total(self):
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
        assert usage.total_tokens == 150

    def test_token_usage_explicit_total_preserved(self):
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=200)
        # total_tokens is already non-zero, validator should not overwrite
        assert usage.total_tokens == 200

    def test_token_usage_cache_hit_ratio(self):
        usage = TokenUsage(prompt_tokens=1000, cached_tokens=800)
        assert usage.cache_hit_ratio == pytest.approx(0.8)

    def test_token_usage_no_cache(self):
        usage = TokenUsage(prompt_tokens=500, completion_tokens=200)
        assert usage.cache_hit_ratio == 0.0

    def test_token_usage_estimated_cost_with_explicit(self):
        usage = TokenUsage(
            prompt_tokens=1000,
            completion_tokens=500,
            cost_usd=0.05,
        )
        assert usage.estimated_cost == 0.05

    def test_token_usage_estimated_cost_fallback(self):
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=1000)
        # fallback: $0.01/1K input + $0.03/1K output
        expected = 1000 * 0.00001 + 1000 * 0.00003
        assert usage.estimated_cost == pytest.approx(expected)

    def test_token_usage_with_model_name(self):
        usage = TokenUsage(
            prompt_tokens=500,
            completion_tokens=200,
            model_name="claude-3-opus",
        )
        assert usage.model_name == "claude-3-opus"


# ============================================================
# 5. ToolCall model tests (from tool_call.py)
# ============================================================

class TestToolCall:
    """工具调用模型测试"""

    def test_create_tool_call_defaults(self):
        tc = ToolCall(tool_name="search")
        assert tc.tool_name == "search"
        assert tc.tool_type == ToolType.CUSTOM.value
        assert tc.call_id is not None
        assert tc.success is True
        assert tc.input_tokens == 0
        assert tc.output_tokens == 0
        assert tc.latency_ms == 0.0
        assert tc.retry_count == 0
        assert tc.metadata == {}

    def test_tool_call_with_all_fields(self):
        tc = ToolCall(
            tool_name="execute_sql",
            tool_type=ToolType.DATABASE,
            input_summary="SELECT * FROM users LIMIT 10",
            output_summary="10 rows returned",
            input_tokens=50,
            output_tokens=200,
            latency_ms=125.5,
            success=True,
            retry_count=1,
            metadata={"db": "analytics"},
        )
        assert tc.tool_type == ToolType.DATABASE.value
        assert tc.input_summary is not None
        assert tc.output_summary is not None
        assert tc.latency_ms == 125.5
        assert tc.metadata["db"] == "analytics"

    def test_tool_call_failed(self):
        tc = ToolCall(
            tool_name="http_fetch",
            tool_type=ToolType.NETWORK,
            success=False,
            error_type="ConnectionError",
            error_message="Connection refused",
        )
        assert tc.success is False
        assert tc.error_type == "ConnectionError"
        assert tc.error_message == "Connection refused"

    def test_tool_type_enum_values(self):
        assert ToolType.API == "api"
        assert ToolType.DATABASE == "database"
        assert ToolType.FILE_SYSTEM == "file_system"
        assert ToolType.CODE_EXECUTION == "code_execution"
        assert ToolType.NETWORK == "network"
        assert ToolType.SEARCH == "search"
        assert ToolType.CALCULATION == "calculation"
        assert ToolType.VISUALIZATION == "visualization"
        assert ToolType.CUSTOM == "custom"

    def test_tool_call_unique_ids(self):
        tc1 = ToolCall(tool_name="a")
        tc2 = ToolCall(tool_name="a")
        assert tc1.call_id != tc2.call_id

    def test_tool_call_json_serialization(self):
        tc = ToolCall(
            tool_name="read_file",
            tool_type=ToolType.FILE_SYSTEM,
            input_summary="path=/tmp/test.txt",
        )
        data = tc.model_dump()
        assert data["tool_name"] == "read_file"
        assert data["tool_type"] == "file_system"
        assert "call_id" in data


# ============================================================
# 6. AgentSession model tests
# ============================================================

class TestTaskStatus:
    """任务状态枚举测试"""

    def test_task_status_values(self):
        assert TaskStatus.PLANNING == "planning"
        assert TaskStatus.EXECUTING == "executing"
        assert TaskStatus.WAITING == "waiting"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.TIMEOUT == "timeout"
        assert TaskStatus.CANCELLED == "cancelled"

    def test_task_priority_values(self):
        assert TaskPriority.LOW == "low"
        assert TaskPriority.NORMAL == "normal"
        assert TaskPriority.HIGH == "high"
        assert TaskPriority.CRITICAL == "critical"


class TestAgentSession:
    """Agent 会话/任务模型测试"""

    def test_create_agent_session(self):
        session = AgentSession(
            agent_id="agent_001",
            agent_type="llm_agent",
        )
        assert session.agent_id == "agent_001"
        assert session.session_id is not None
        assert session.status == TaskStatus.PLANNING.value
        assert session.priority == TaskPriority.NORMAL.value
        assert session.total_events == 0
        assert session.total_tool_calls == 0
        assert session.total_llm_calls == 0
        assert session.total_tokens == 0
        assert session.total_cost_usd == 0.0

    def test_agent_session_defaults(self):
        session = AgentSession(
            agent_id="agent_001",
            agent_type="tool_agent",
        )
        assert session.task_id is None
        assert session.goal is None
        assert session.plan == []
        assert session.parent_session_id is None
        assert session.delegated_to == []
        assert session.end_time is None
        assert session.deadline is None
        assert session.result_summary is None
        assert session.error_summary is None

    def test_agent_session_with_all_fields(self):
        now = datetime.now(UTC)
        session = AgentSession(
            agent_id="agent_001",
            agent_type="workflow_agent",
            task_id="task_001",
            goal="Analyze customer feedback",
            plan=["Collect data", "Run sentiment analysis", "Generate report"],
            status=TaskStatus.EXECUTING,
            priority=TaskPriority.HIGH,
            parent_session_id="parent_001",
            delegated_to=["sub_agent_1", "sub_agent_2"],
            total_events=50,
            total_tool_calls=10,
            total_llm_calls=5,
            total_tokens=8000,
            total_cost_usd=0.25,
            start_time=now,
            deadline=now + timedelta(hours=1),
        )
        assert session.goal == "Analyze customer feedback"
        assert len(session.plan) == 3
        assert session.priority == TaskPriority.HIGH.value
        assert len(session.delegated_to) == 2

    def test_agent_session_duration_with_end_time(self):
        start = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        end = datetime(2024, 1, 1, 12, 0, 5, tzinfo=UTC)
        session = AgentSession(
            agent_id="a1",
            agent_type="llm_agent",
            start_time=start,
            end_time=end,
        )
        assert session.duration_ms == pytest.approx(5000.0)

    def test_agent_session_duration_without_end_time(self):
        session = AgentSession(
            agent_id="a1",
            agent_type="llm_agent",
        )
        assert session.duration_ms is None

    def test_agent_session_is_active(self):
        for status in (TaskStatus.PLANNING, TaskStatus.EXECUTING, TaskStatus.WAITING):
            session = AgentSession(
                agent_id="a1",
                agent_type="llm_agent",
                status=status,
            )
            assert session.is_active is True

    def test_agent_session_is_not_active(self):
        for status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELLED):
            session = AgentSession(
                agent_id="a1",
                agent_type="llm_agent",
                status=status,
            )
            assert session.is_active is False

    def test_agent_session_unique_ids(self):
        s1 = AgentSession(agent_id="a1", agent_type="llm_agent")
        s2 = AgentSession(agent_id="a1", agent_type="llm_agent")
        assert s1.session_id != s2.session_id

    def test_agent_session_status_transition(self):
        session = AgentSession(
            agent_id="a1",
            agent_type="llm_agent",
        )
        assert session.status == TaskStatus.PLANNING.value
        session.status = TaskStatus.EXECUTING.value
        assert session.status == TaskStatus.EXECUTING.value
        session.status = TaskStatus.COMPLETED.value
        assert session.status == TaskStatus.COMPLETED.value
        assert session.is_active is False


# ============================================================
# 7. AgentTrace / TraceSpan model tests
# ============================================================

class TestTraceSpan:
    """追踪 Span 模型测试"""

    def test_create_trace_span(self):
        span = TraceSpan(
            trace_id="trace_001",
            name="llm_call",
        )
        assert span.trace_id == "trace_001"
        assert span.name == "llm_call"
        assert span.span_id is not None
        assert span.kind == SpanKind.AGENT.value
        assert span.status == SpanStatus.OK.value
        assert span.parent_span_id is None

    def test_trace_span_duration_with_end(self):
        start = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        end = datetime(2024, 1, 1, 12, 0, 2, tzinfo=UTC)
        span = TraceSpan(
            trace_id="t1",
            name="tool_exec",
            start_time=start,
            end_time=end,
        )
        assert span.duration_ms == pytest.approx(2000.0)

    def test_trace_span_duration_without_end(self):
        span = TraceSpan(trace_id="t1", name="running")
        assert span.duration_ms is None

    def test_trace_span_with_attributes(self):
        span = TraceSpan(
            trace_id="t1",
            name="db_query",
            kind=SpanKind.TOOL,
            agent_id="agent_001",
            attributes={"db.name": "analytics", "db.operation": "select"},
            status=SpanStatus.ERROR,
            status_message="Connection timeout",
        )
        assert span.kind == SpanKind.TOOL.value
        assert span.attributes["db.name"] == "analytics"
        assert span.status == SpanStatus.ERROR.value

    def test_span_kind_values(self):
        assert SpanKind.AGENT == "agent"
        assert SpanKind.LLM == "llm"
        assert SpanKind.TOOL == "tool"
        assert SpanKind.CHAIN == "chain"
        assert SpanKind.RETRIEVER == "retriever"
        assert SpanKind.PARSER == "parser"

    def test_span_status_values(self):
        assert SpanStatus.OK == "ok"
        assert SpanStatus.ERROR == "error"
        assert SpanStatus.TIMEOUT == "timeout"
        assert SpanStatus.CANCELLED == "cancelled"


class TestAgentTrace:
    """Agent 执行追踪模型测试"""

    def test_create_agent_trace(self):
        trace = AgentTrace(agent_id="agent_001")
        assert trace.agent_id == "agent_001"
        assert trace.trace_id is not None
        assert trace.spans == []
        assert trace.total_tokens == 0
        assert trace.total_cost_usd == 0.0
        assert trace.error_count == 0
        assert trace.has_timeout is False

    def test_agent_trace_duration(self):
        start = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        end = datetime(2024, 1, 1, 12, 0, 10, tzinfo=UTC)
        trace = AgentTrace(
            agent_id="a1",
            start_time=start,
            end_time=end,
        )
        assert trace.duration_ms == pytest.approx(10000.0)

    def test_agent_trace_duration_no_end(self):
        trace = AgentTrace(agent_id="a1")
        assert trace.duration_ms is None

    def test_agent_trace_add_span(self):
        trace = AgentTrace(agent_id="a1")
        span = TraceSpan(trace_id=trace.trace_id, name="step1")
        trace.add_span(span)
        assert trace.span_count == 1
        assert trace.error_count == 0

    def test_agent_trace_add_error_span(self):
        trace = AgentTrace(agent_id="a1")
        span = TraceSpan(
            trace_id=trace.trace_id,
            name="failed_call",
            status=SpanStatus.ERROR,
        )
        trace.add_span(span)
        assert trace.span_count == 1
        assert trace.error_count == 1

    def test_agent_trace_add_timeout_span(self):
        trace = AgentTrace(agent_id="a1")
        span = TraceSpan(
            trace_id=trace.trace_id,
            name="slow_call",
            status=SpanStatus.TIMEOUT,
        )
        trace.add_span(span)
        assert trace.has_timeout is True

    def test_agent_trace_get_span(self):
        trace = AgentTrace(agent_id="a1")
        span = TraceSpan(trace_id=trace.trace_id, name="my_span", span_id="span_xyz")
        trace.add_span(span)
        found = trace.get_span("span_xyz")
        assert found is not None
        assert found.name == "my_span"

    def test_agent_trace_get_span_not_found(self):
        trace = AgentTrace(agent_id="a1")
        assert trace.get_span("nonexistent") is None

    def test_agent_trace_get_children(self):
        trace = AgentTrace(agent_id="a1")
        parent = TraceSpan(
            trace_id=trace.trace_id,
            name="parent",
            span_id="parent_1",
        )
        child1 = TraceSpan(
            trace_id=trace.trace_id,
            name="child_1",
            span_id="c1",
            parent_span_id="parent_1",
        )
        child2 = TraceSpan(
            trace_id=trace.trace_id,
            name="child_2",
            span_id="c2",
            parent_span_id="parent_1",
        )
        unrelated = TraceSpan(
            trace_id=trace.trace_id,
            name="other",
            span_id="other_1",
        )
        for s in (parent, child1, child2, unrelated):
            trace.add_span(s)

        children = trace.get_children("parent_1")
        assert len(children) == 2
        names = {c.name for c in children}
        assert names == {"child_1", "child_2"}

    def test_agent_trace_with_all_fields(self):
        trace = AgentTrace(
            agent_id="agent_001",
            session_id="sess_001",
            task_id="task_001",
            root_span_id="root_1",
            total_tokens=5000,
            total_cost_usd=0.15,
            error_count=2,
            has_timeout=True,
        )
        assert trace.session_id == "sess_001"
        assert trace.root_span_id == "root_1"
        assert trace.total_tokens == 5000
        assert trace.has_timeout is True


# ============================================================
# 8. AgentCapability model tests
# ============================================================

class TestAgentCapability:
    """Agent 能力评估模型测试"""

    def test_create_agent_capability(self):
        cap = AgentCapability(
            agent_id="agent_001",
            capability_name="sql_generation",
            category=CapabilityCategory.CODE_GENERATION,
        )
        assert cap.agent_id == "agent_001"
        assert cap.capability_name == "sql_generation"
        assert cap.level == CapabilityLevel.NOVICE.value
        assert cap.success_rate == 0.0
        assert cap.total_invocations == 0
        assert cap.supported_tools == []
        assert cap.supported_models == []

    def test_capability_level_values(self):
        assert CapabilityLevel.NOVICE == "novice"
        assert CapabilityLevel.INTERMEDIATE == "intermediate"
        assert CapabilityLevel.ADVANCED == "advanced"
        assert CapabilityLevel.EXPERT == "expert"

    def test_capability_category_values(self):
        assert CapabilityCategory.REASONING == "reasoning"
        assert CapabilityCategory.TOOL_USE == "tool_use"
        assert CapabilityCategory.CODE_GENERATION == "code_generation"
        assert CapabilityCategory.DATA_ANALYSIS == "data_analysis"
        assert CapabilityCategory.COMMUNICATION == "communication"
        assert CapabilityCategory.PLANNING == "planning"
        assert CapabilityCategory.RESEARCH == "research"
        assert CapabilityCategory.CREATIVE == "creative"
        assert CapabilityCategory.DOMAIN_SPECIFIC == "domain_specific"

    def test_update_stats_success(self):
        cap = AgentCapability(
            agent_id="a1",
            capability_name="code_gen",
            category=CapabilityCategory.CODE_GENERATION,
        )
        cap.update_stats(success=True, latency_ms=200.0, quality=0.9)
        assert cap.total_invocations == 1
        assert cap.successful_invocations == 1
        assert cap.failed_invocations == 0
        assert cap.success_rate == 1.0
        assert cap.avg_latency_ms == 200.0
        assert cap.avg_output_quality == 0.9

    def test_update_stats_failure(self):
        cap = AgentCapability(
            agent_id="a1",
            capability_name="code_gen",
            category=CapabilityCategory.CODE_GENERATION,
        )
        cap.update_stats(success=False, latency_ms=500.0)
        assert cap.total_invocations == 1
        assert cap.successful_invocations == 0
        assert cap.failed_invocations == 1
        assert cap.success_rate == 0.0

    def test_update_stats_level_progression(self):
        cap = AgentCapability(
            agent_id="a1",
            capability_name="sql_gen",
            category=CapabilityCategory.CODE_GENERATION,
        )
        # Simulate 100 successful invocations to reach EXPERT
        for _ in range(100):
            cap.update_stats(success=True, latency_ms=100.0, quality=0.95)

        assert cap.total_invocations == 100
        assert cap.success_rate == 1.0
        assert cap.level == CapabilityLevel.EXPERT.value

    def test_update_stats_intermediate_level(self):
        cap = AgentCapability(
            agent_id="a1",
            capability_name="data_analysis",
            category=CapabilityCategory.DATA_ANALYSIS,
        )
        # 20 invocations, 15 successful = 75% -> INTERMEDIATE
        for _ in range(15):
            cap.update_stats(success=True, latency_ms=100.0)
        for _ in range(5):
            cap.update_stats(success=False, latency_ms=200.0)

        assert cap.total_invocations == 20
        assert cap.success_rate == pytest.approx(0.75)
        assert cap.level == CapabilityLevel.INTERMEDIATE.value

    def test_update_stats_latency_running_average(self):
        cap = AgentCapability(
            agent_id="a1",
            capability_name="test",
            category=CapabilityCategory.REASONING,
        )
        cap.update_stats(success=True, latency_ms=100.0)
        first_avg = cap.avg_latency_ms
        assert first_avg == 100.0

        cap.update_stats(success=True, latency_ms=300.0)
        # running avg: 100 * 0.9 + 300 * 0.1 = 120
        assert cap.avg_latency_ms == pytest.approx(120.0)

    def test_capability_with_supported_tools(self):
        cap = AgentCapability(
            agent_id="a1",
            capability_name="web_search",
            category=CapabilityCategory.TOOL_USE,
            supported_tools=["google_search", "bing_search", "web_scraper"],
            supported_models=["gpt-4", "claude-3"],
            max_complexity="high",
        )
        assert len(cap.supported_tools) == 3
        assert len(cap.supported_models) == 2
        assert cap.max_complexity == "high"


class TestAgentCapabilityMap:
    """Agent 能力图谱测试"""

    def test_create_capability_map(self):
        cmap = AgentCapabilityMap(agent_id="agent_001")
        assert cmap.capabilities == {}
        assert cmap.overall_score == 0.0

    def test_add_capability(self):
        cmap = AgentCapabilityMap(agent_id="agent_001")
        cap = AgentCapability(
            agent_id="agent_001",
            capability_name="sql_gen",
            category=CapabilityCategory.CODE_GENERATION,
            success_rate=0.85,
        )
        cmap.add_capability(cap)
        assert "sql_gen" in cmap.capabilities
        assert cmap.overall_score == pytest.approx(0.85)

    def test_get_capability(self):
        cmap = AgentCapabilityMap(agent_id="agent_001")
        cap = AgentCapability(
            agent_id="agent_001",
            capability_name="reasoning",
            category=CapabilityCategory.REASONING,
            success_rate=0.9,
        )
        cmap.add_capability(cap)
        found = cmap.get_capability("reasoning")
        assert found is not None
        assert found.success_rate == pytest.approx(0.9)

    def test_get_capability_not_found(self):
        cmap = AgentCapabilityMap(agent_id="agent_001")
        assert cmap.get_capability("nonexistent") is None

    def test_overall_score_multiple_capabilities(self):
        cmap = AgentCapabilityMap(agent_id="agent_001")
        for name, rate in [("a", 0.8), ("b", 0.6), ("c", 1.0)]:
            cap = AgentCapability(
                agent_id="agent_001",
                capability_name=name,
                category=CapabilityCategory.REASONING,
                success_rate=rate,
            )
            cmap.add_capability(cap)
        expected = (0.8 + 0.6 + 1.0) / 3
        assert cmap.overall_score == pytest.approx(expected)


# ============================================================
# 9. AgentAggregation model tests
# ============================================================

class TestAgentAggregation:
    """Agent 聚合结果模型测试"""

    def test_create_agent_aggregation(self):
        now = datetime.now(UTC)
        agg = AgentAggregation(
            agent_id="agent_001",
            window_start=now,
            window_end=now + timedelta(hours=1),
        )
        assert agg.aggregation_id is not None
        assert agg.agent_id == "agent_001"
        assert agg.event_count == 0
        assert agg.tool_call_count == 0
        assert agg.total_cost_usd == 0.0
        assert agg.success_rate == 0.0
        assert agg.tool_usage == {}
        assert agg.model_usage == {}
        assert agg.anomaly_score == 0.0
        assert agg.anomaly_flags == []

    def test_aggregation_with_all_fields(self):
        now = datetime.now(UTC)
        agg = AgentAggregation(
            agent_id="agent_001",
            window_start=now,
            window_end=now + timedelta(hours=1),
            event_count=100,
            tool_call_count=30,
            tool_result_count=28,
            llm_request_count=20,
            llm_response_count=20,
            error_count=2,
            timeout_count=1,
            delegation_count=5,
            total_prompt_tokens=15000,
            total_completion_tokens=8000,
            total_tokens=23000,
            cached_tokens=5000,
            total_cost_usd=0.75,
            avg_latency_ms=350.0,
            p95_latency_ms=1200.0,
            p99_latency_ms=2500.0,
            max_latency_ms=5000.0,
            success_rate=0.95,
            error_rate=0.02,
            tool_usage={"search": 15, "db_query": 10, "file_read": 5},
            model_usage={"gpt-4": 15, "claude-3": 5},
            unique_sessions=8,
            unique_tasks=5,
            anomaly_score=0.1,
            anomaly_flags=["slow_tool_call"],
        )
        assert agg.event_count == 100
        assert agg.tool_call_count == 30
        assert agg.total_tokens == 23000
        assert agg.cached_tokens == 5000
        assert agg.success_rate == 0.95
        assert len(agg.tool_usage) == 3
        assert agg.tool_usage["search"] == 15
        assert len(agg.model_usage) == 2
        assert agg.anomaly_score == 0.1
        assert "slow_tool_call" in agg.anomaly_flags


class TestCostBreakdown:
    """成本细分模型测试"""

    def test_create_cost_breakdown(self):
        now = datetime.now(UTC)
        cb = CostBreakdown(
            agent_id="agent_001",
            period_start=now,
            period_end=now + timedelta(days=1),
        )
        assert cb.total_cost_usd == 0.0
        assert cb.total_tokens == 0
        assert cb.cost_by_model == {}

    def test_cost_breakdown_with_data(self):
        now = datetime.now(UTC)
        cb = CostBreakdown(
            agent_id="agent_001",
            period_start=now,
            period_end=now + timedelta(days=7),
            cost_by_model={"gpt-4": 5.0, "claude-3": 3.0},
            tokens_by_model={"gpt-4": 100000, "claude-3": 60000},
            cost_by_tool={"search": 1.5, "db_query": 0.5},
            calls_by_tool={"search": 50, "db_query": 30},
            total_cost_usd=8.0,
            total_tokens=160000,
            total_tool_calls=80,
            total_llm_calls=40,
            cost_per_success=0.16,
            tokens_per_success=3200,
        )
        assert cb.cost_by_model["gpt-4"] == 5.0
        assert cb.total_tool_calls == 80
        assert cb.cost_per_success == 0.16


class TestPerformanceMetrics:
    """性能指标模型测试"""

    def test_create_performance_metrics(self):
        now = datetime.now(UTC)
        pm = PerformanceMetrics(
            agent_id="agent_001",
            period_start=now,
            period_end=now + timedelta(hours=1),
        )
        assert pm.avg_latency_ms == 0.0
        assert pm.success_rate == 0.0
        assert pm.tasks_completed == 0

    def test_performance_metrics_with_data(self):
        now = datetime.now(UTC)
        pm = PerformanceMetrics(
            agent_id="agent_001",
            period_start=now,
            period_end=now + timedelta(hours=1),
            avg_latency_ms=250.0,
            p50_latency_ms=180.0,
            p95_latency_ms=800.0,
            p99_latency_ms=1500.0,
            events_per_second=10.5,
            tool_calls_per_minute=30.0,
            llm_calls_per_minute=12.0,
            success_rate=0.97,
            error_rate=0.02,
            timeout_rate=0.01,
            retry_rate=0.03,
            tasks_completed=45,
            tasks_failed=2,
            avg_task_duration_ms=5000.0,
        )
        assert pm.p95_latency_ms == 800.0
        assert pm.success_rate == 0.97
        assert pm.tasks_completed == 45


# ============================================================
# 10. AgentAlert model tests
# ============================================================

class TestAgentAlertType:
    """Agent 告警类型枚举测试"""

    def test_alert_type_loop_anomalies(self):
        assert AgentAlertType.DEAD_LOOP == "dead_loop"
        assert AgentAlertType.INFINITE_RETRY == "infinite_retry"
        assert AgentAlertType.OSCILLATION == "oscillation"

    def test_alert_type_cost_anomalies(self):
        assert AgentAlertType.COST_SPIKE == "cost_spike"
        assert AgentAlertType.BUDGET_EXCEEDED == "budget_exceeded"
        assert AgentAlertType.TOKEN_EXPLOSION == "token_explosion"

    def test_alert_type_security_anomalies(self):
        assert AgentAlertType.PROMPT_INJECTION == "prompt_injection"
        assert AgentAlertType.TOOL_ABUSE == "tool_abuse"
        assert AgentAlertType.DATA_EXFILTRATION == "data_exfiltration"
        assert AgentAlertType.CAPABILITY_DRIFT == "capability_drift"

    def test_alert_type_performance_anomalies(self):
        assert AgentAlertType.TIMEOUT_CASCADE == "timeout_cascade"
        assert AgentAlertType.LATENCY_DEGRADATION == "latency_degradation"
        assert AgentAlertType.ERROR_RATE_SPIKE == "error_rate_spike"

    def test_alert_type_multi_agent_anomalies(self):
        assert AgentAlertType.RESOURCE_CONTENTION == "resource_contention"
        assert AgentAlertType.CASCADING_FAILURE == "cascading_failure"
        assert AgentAlertType.DEADLOCK == "deadlock"

    def test_alert_type_compliance(self):
        assert AgentAlertType.POLICY_VIOLATION == "policy_violation"
        assert AgentAlertType.UNAUTHORIZED_ACCESS == "unauthorized_access"

    def test_alert_severity_values(self):
        assert AlertSeverity.LOW == "low"
        assert AlertSeverity.MEDIUM == "medium"
        assert AlertSeverity.HIGH == "high"
        assert AlertSeverity.CRITICAL == "critical"

    def test_auto_action_values(self):
        assert AutoAction.NONE == "none"
        assert AutoAction.LOG == "log"
        assert AutoAction.THROTTLE == "throttle"
        assert AutoAction.PAUSE == "pause"
        assert AutoAction.KILL == "kill"
        assert AutoAction.ROLLBACK == "rollback"
        assert AutoAction.NOTIFY == "notify"
        assert AutoAction.ESCALATE == "escalate"


class TestAgentAlert:
    """Agent 告警模型测试"""

    def test_create_agent_alert(self):
        alert = AgentAlert(
            alert_type=AgentAlertType.DEAD_LOOP,
            agent_id="agent_001",
            message="Agent stuck in loop",
        )
        assert alert.alert_id is not None
        assert alert.alert_type == AgentAlertType.DEAD_LOOP.value
        assert alert.severity == AlertSeverity.MEDIUM.value
        assert alert.resolved is False
        assert alert.auto_action == AutoAction.NONE.value
        assert alert.action_taken is False
        assert alert.escalated is False
        assert alert.occurrence_count == 1

    def test_alert_with_critical_severity(self):
        alert = AgentAlert(
            alert_type=AgentAlertType.PROMPT_INJECTION,
            agent_id="agent_001",
            message="Prompt injection detected",
            severity=AlertSeverity.CRITICAL,
            description="User attempted to inject system prompt override",
            auto_action=AutoAction.KILL,
        )
        assert alert.severity == AlertSeverity.CRITICAL.value
        assert alert.auto_action == AutoAction.KILL.value
        assert alert.description is not None

    def test_alert_with_context(self):
        alert = AgentAlert(
            alert_type=AgentAlertType.COST_SPIKE,
            agent_id="agent_001",
            message="Cost exceeded threshold",
            trace_id="trace_001",
            session_id="sess_001",
            task_id="task_001",
            trigger_data={"hourly_cost": 15.0},
            trigger_threshold=10.0,
            trigger_value=15.0,
        )
        assert alert.trace_id == "trace_001"
        assert alert.trigger_data["hourly_cost"] == 15.0
        assert alert.trigger_threshold == 10.0
        assert alert.trigger_value == 15.0

    def test_alert_resolution(self):
        now = datetime.now(UTC)
        alert = AgentAlert(
            alert_type=AgentAlertType.LATENCY_DEGRADATION,
            agent_id="agent_001",
            message="Latency spike",
            resolved=True,
            resolved_by="auto",
            resolved_at=now,
            resolution_notes="Auto-resolved after latency returned to normal",
        )
        assert alert.resolved is True
        assert alert.resolved_by == "auto"
        assert alert.resolved_at == now

    def test_alert_escalation(self):
        now = datetime.now(UTC)
        alert = AgentAlert(
            alert_type=AgentAlertType.DATA_EXFILTRATION,
            agent_id="agent_001",
            message="Data exfiltration attempt",
            escalated=True,
            escalated_to="security_team",
            escalated_at=now,
        )
        assert alert.escalated is True
        assert alert.escalated_to == "security_team"

    def test_alert_occurrence_tracking(self):
        alert = AgentAlert(
            alert_type=AgentAlertType.ERROR_RATE_SPIKE,
            agent_id="agent_001",
            message="Error rate high",
            occurrence_count=15,
            first_seen=datetime(2024, 1, 1, tzinfo=UTC),
            last_seen=datetime.now(UTC),
        )
        assert alert.occurrence_count == 15
        assert alert.first_seen is not None
        assert alert.last_seen is not None

    def test_alert_json_serialization(self):
        alert = AgentAlert(
            alert_type=AgentAlertType.TOOL_ABUSE,
            agent_id="agent_001",
            message="Tool abuse detected",
        )
        data = alert.model_dump()
        assert "alert_id" in data
        assert data["alert_type"] == "tool_abuse"
        assert data["message"] == "Tool abuse detected"


class TestAlertRule:
    """告警规则定义测试"""

    def test_create_alert_rule(self):
        rule = AlertRule(
            name="High Error Rate",
            alert_type=AgentAlertType.ERROR_RATE_SPIKE,
            metric="error_rate",
            operator=">",
            threshold=0.1,
        )
        assert rule.rule_id is not None
        assert rule.name == "High Error Rate"
        assert rule.enabled is True
        assert rule.cooldown_seconds == 300
        assert rule.max_alerts_per_hour == 10

    def test_alert_rule_with_all_fields(self):
        rule = AlertRule(
            name="Cost Budget Alert",
            description="Alert when hourly cost exceeds budget",
            alert_type=AgentAlertType.BUDGET_EXCEEDED,
            severity=AlertSeverity.HIGH,
            metric="cost_per_hour",
            operator=">=",
            threshold=50.0,
            window_seconds=3600,
            auto_action=AutoAction.THROTTLE,
            notify_channels=["slack", "email"],
            enabled=True,
            cooldown_seconds=600,
            max_alerts_per_hour=5,
            agent_ids=["agent_001", "agent_002"],
            agent_types=["llm_agent"],
        )
        assert rule.severity == AlertSeverity.HIGH.value
        assert rule.auto_action == AutoAction.THROTTLE.value
        assert len(rule.notify_channels) == 2
        assert len(rule.agent_ids) == 2
        assert rule.window_seconds == 3600


# ============================================================
# 11. AgentProfile model tests
# ============================================================

class TestAgentProfile:
    """Agent 画像模型测试"""

    def test_create_agent_profile(self):
        profile = AgentProfile(agent_id="agent_001")
        assert profile.agent_id == "agent_001"
        assert profile.status == AgentStatus.ACTIVE.value
        assert profile.safety_rating == SafetyRating.STANDARD.value
        assert profile.cost_tier == CostTier.STANDARD.value
        assert profile.risk_score == 0.0
        assert profile.capabilities == []
        assert profile.behavior_tags == []
        assert profile.performance_tags == []
        assert profile.safety_tags == []

    def test_agent_status_values(self):
        assert AgentStatus.ACTIVE == "active"
        assert AgentStatus.IDLE == "idle"
        assert AgentStatus.PAUSED == "paused"
        assert AgentStatus.ERROR == "error"
        assert AgentStatus.TERMINATED == "terminated"
        assert AgentStatus.DEPRECATED == "deprecated"

    def test_safety_rating_values(self):
        assert SafetyRating.TRUSTED == "trusted"
        assert SafetyRating.STANDARD == "standard"
        assert SafetyRating.RESTRICTED == "restricted"
        assert SafetyRating.QUARANTINED == "quarantined"
        assert SafetyRating.BLOCKED == "blocked"

    def test_cost_tier_values(self):
        assert CostTier.FREE == "free"
        assert CostTier.BASIC == "basic"
        assert CostTier.STANDARD == "standard"
        assert CostTier.PREMIUM == "premium"
        assert CostTier.UNLIMITED == "unlimited"

    def test_agent_profile_with_all_fields(self):
        now = datetime.now(UTC)
        profile = AgentProfile(
            agent_id="agent_001",
            agent_name="Customer Support Bot",
            agent_type="llm_agent",
            description="Handles customer inquiries",
            model_name="gpt-4",
            model_version="2024-06",
            framework="langchain",
            owner="team_cs",
            organization="acme_corp",
            purpose="Customer support automation",
            status=AgentStatus.ACTIVE,
            safety_rating=SafetyRating.TRUSTED,
            cost_tier=CostTier.PREMIUM,
            capabilities=["reasoning", "tool_use", "communication"],
            supported_tools=["search", "email", "crm_lookup"],
            max_context_window=128000,
            behavior_tags=["polite", "efficient"],
            performance_tags=["fast_response", "high_accuracy"],
            safety_tags=["compliant", "audited"],
            custom_tags={"department": "support", "region": "us-east"},
            risk_score=0.15,
            risk_factors=["high_cost", "external_api_dependency"],
            create_time=now,
            update_time=now,
            first_seen=now,
            last_active=now,
        )
        assert profile.agent_name == "Customer Support Bot"
        assert profile.model_name == "gpt-4"
        assert profile.framework == "langchain"
        assert profile.status == AgentStatus.ACTIVE.value
        assert profile.safety_rating == SafetyRating.TRUSTED.value
        assert profile.cost_tier == CostTier.PREMIUM.value
        assert len(profile.capabilities) == 3
        assert len(profile.supported_tools) == 3
        assert profile.max_context_window == 128000
        assert profile.risk_score == 0.15
        assert len(profile.risk_factors) == 2
        assert profile.custom_tags["department"] == "support"


# ============================================================
# 12. AgentStat model tests
# ============================================================

class TestAgentStat:
    """Agent 统计模型测试"""

    def test_create_agent_stat(self):
        stat = AgentStat(agent_id="agent_001")
        assert stat.agent_id == "agent_001"
        assert stat.total_events == 0
        assert stat.total_sessions == 0
        assert stat.total_tasks == 0
        assert stat.total_tool_calls == 0
        assert stat.total_llm_calls == 0
        assert stat.total_delegations == 0
        assert stat.total_prompt_tokens == 0
        assert stat.total_completion_tokens == 0
        assert stat.total_tokens == 0
        assert stat.total_cost_usd == 0.0

    def test_agent_stat_with_all_fields(self):
        now = datetime.now(UTC)
        stat = AgentStat(
            agent_id="agent_001",
            # Totals
            total_events=5000,
            total_sessions=200,
            total_tasks=150,
            total_tool_calls=800,
            total_llm_calls=500,
            total_delegations=25,
            # Token totals
            total_prompt_tokens=500000,
            total_completion_tokens=200000,
            total_tokens=700000,
            total_cached_tokens=150000,
            # Cost totals
            total_cost_usd=25.50,
            # Time window events
            events_1h=50,
            events_1d=500,
            events_7d=2500,
            events_30d=5000,
            # Time window tokens
            tokens_1h=5000,
            tokens_1d=50000,
            tokens_7d=250000,
            tokens_30d=700000,
            # Time window cost
            cost_1h=0.50,
            cost_1d=5.0,
            cost_7d=18.0,
            cost_30d=25.50,
            # Time window tasks
            tasks_1d=5,
            tasks_7d=30,
            tasks_30d=150,
            # Performance
            avg_latency_ms=320.0,
            p95_latency_ms=1200.0,
            success_rate=0.96,
            error_rate=0.03,
            timeout_rate=0.01,
            # Recent activity
            last_event_time=now,
            last_tool_call_time=now - timedelta(minutes=5),
            last_llm_call_time=now - timedelta(minutes=2),
            last_error_time=now - timedelta(hours=1),
            last_task_completion_time=now - timedelta(minutes=30),
            update_time=now,
        )
        assert stat.total_events == 5000
        assert stat.total_cost_usd == 25.50
        assert stat.events_1h == 50
        assert stat.events_30d == 5000
        assert stat.tokens_7d == 250000
        assert stat.cost_1d == 5.0
        assert stat.tasks_30d == 150
        assert stat.success_rate == 0.96
        assert stat.last_event_time == now
        assert stat.last_error_time is not None


class TestAgentComparison:
    """Agent 对比分析模型测试"""

    def test_create_agent_comparison(self):
        comp = AgentComparison(agent_ids=["a1", "a2", "a3"])
        assert len(comp.agent_ids) == 3
        assert comp.metrics == {}
        assert comp.rankings == {}
        assert comp.insights == []

    def test_agent_comparison_with_data(self):
        comp = AgentComparison(
            agent_ids=["a1", "a2"],
            metrics={
                "a1": {"success_rate": 0.95, "avg_latency": 200},
                "a2": {"success_rate": 0.88, "avg_latency": 150},
            },
            rankings={
                "success_rate": ["a1", "a2"],
                "avg_latency": ["a2", "a1"],
            },
            insights=["Agent a1 has better success rate but higher latency"],
        )
        assert comp.metrics["a1"]["success_rate"] == 0.95
        assert comp.rankings["success_rate"][0] == "a1"
        assert len(comp.insights) == 1
