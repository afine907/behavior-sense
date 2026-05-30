"""
边界情况和鲁棒性测试
"""
import pytest
from behavior_core.models.agent_event import AgentBehavior, AgentEventType, AgentType
from behavior_core.models.token_usage import TokenUsage
from behavior_core.models.tool_call import ToolCall, ToolType
from behavior_core.models.agent_session import AgentSession, TaskStatus
from behavior_core.models.agent_trace import AgentTrace, TraceSpan


class TestAgentBehaviorEdgeCases:
    """AgentBehavior边界测试"""

    def test_empty_agent_id(self):
        """空agent_id应该抛出验证错误"""
        with pytest.raises(Exception):
            AgentBehavior(agent_id="", event_type=AgentEventType.TOOL_CALL)

    def test_very_long_agent_id(self):
        """超长agent_id应该抛出验证错误"""
        with pytest.raises(Exception):
            AgentBehavior(agent_id="a" * 1000, event_type=AgentEventType.TOOL_CALL)

    def test_special_characters_in_agent_id(self):
        """特殊字符agent_id应该正常工作"""
        event = AgentBehavior(
            agent_id="agent-001_test.special",
            event_type=AgentEventType.TOOL_CALL,
        )
        assert event.agent_id == "agent-001_test.special"

    def test_unicode_agent_id(self):
        """Unicode agent_id应该正常工作"""
        event = AgentBehavior(
            agent_id="agent-测试-001",
            event_type=AgentEventType.TOOL_CALL,
        )
        assert event.agent_id == "agent-测试-001"

    def test_all_event_types(self):
        """所有事件类型都应该正常工作"""
        for event_type in AgentEventType:
            event = AgentBehavior(
                agent_id="test-agent",
                event_type=event_type,
            )
            assert event.event_type == event_type

    def test_all_agent_types(self):
        """所有Agent类型都应该正常工作"""
        for agent_type in AgentType:
            event = AgentBehavior(
                agent_id="test-agent",
                agent_type=agent_type,
                event_type=AgentEventType.TOOL_CALL,
            )
            assert event.agent_type == agent_type

    def test_none_optional_fields(self):
        """可选字段为None应该正常工作"""
        event = AgentBehavior(
            agent_id="test-agent",
            event_type=AgentEventType.TOOL_CALL,
            trace_id=None,
            session_id=None,
            task_id=None,
            model_name=None,
        )
        assert event.trace_id is None
        assert event.session_id is None

    def test_empty_properties(self):
        """空properties应该正常工作"""
        event = AgentBehavior(
            agent_id="test-agent",
            event_type=AgentEventType.TOOL_CALL,
            properties={},
        )
        assert event.properties == {}

    def test_nested_properties(self):
        """嵌套properties应该正常工作"""
        props = {
            "level1": {"level2": {"level3": [1, 2, 3]}},
            "list": [{"a": 1}, {"b": 2}],
        }
        event = AgentBehavior(
            agent_id="test-agent",
            event_type=AgentEventType.TOOL_CALL,
            properties=props,
        )
        assert event.properties == props


class TestTokenUsageEdgeCases:
    """TokenUsage边界测试"""

    def test_zero_tokens(self):
        """零token应该正常工作"""
        usage = TokenUsage(prompt_tokens=0, completion_tokens=0)
        assert usage.total_tokens == 0

    def test_large_token_counts(self):
        """大token数应该正常工作"""
        usage = TokenUsage(
            prompt_tokens=1000000,
            completion_tokens=500000,
        )
        assert usage.total_tokens == 1500000

    def test_cost_estimation(self):
        """成本估算应该正常工作"""
        usage = TokenUsage(
            prompt_tokens=1000,
            completion_tokens=500,
            model_name="gpt-4",
        )
        assert usage.cost_usd >= 0

    def test_cache_ratio_calculation(self):
        """缓存率计算应该正常工作"""
        usage = TokenUsage(
            prompt_tokens=1000,
            cached_tokens=500,
        )
        assert 0 <= usage.cache_hit_ratio <= 1


class TestToolCallEdgeCases:
    """ToolCall边界测试"""

    def test_all_tool_types(self):
        """所有工具类型都应该正常工作"""
        for tool_type in ToolType:
            call = ToolCall(
                tool_name="test-tool",
                tool_type=tool_type,
            )
            assert call.tool_type == tool_type

    def test_zero_latency(self):
        """零延迟应该正常工作"""
        call = ToolCall(
            tool_name="test-tool",
            latency_ms=0.0,
        )
        assert call.latency_ms == 0.0

    def test_very_high_latency(self):
        """高延迟应该正常工作"""
        call = ToolCall(
            tool_name="test-tool",
            latency_ms=300000.0,  # 5 minutes
        )
        assert call.latency_ms == 300000.0


class TestAgentSessionEdgeCases:
    """AgentSession边界测试"""

    def test_all_task_statuses(self):
        """所有任务状态都应该正常工作"""
        for status in TaskStatus:
            session = AgentSession(
                agent_id="test-agent",
                status=status,
            )
            assert session.status == status

    def test_session_duration(self):
        """会话时长计算应该正常工作"""
        from datetime import UTC, datetime, timedelta
        session = AgentSession(
            agent_id="test-agent",
            start_time=datetime.now(UTC) - timedelta(minutes=5),
            end_time=datetime.now(UTC),
        )
        assert session.duration_ms is not None
        assert session.duration_ms > 0

    def test_active_session_no_end_time(self):
        """活跃会话没有结束时间"""
        session = AgentSession(
            agent_id="test-agent",
            status=TaskStatus.EXECUTING,
        )
        assert session.duration_ms is None
        assert session.is_active is True


class TestAgentTraceEdgeCases:
    """AgentTrace边界测试"""

    def test_empty_trace(self):
        """空trace应该正常工作"""
        trace = AgentTrace(agent_id="test-agent")
        assert trace.span_count == 0
        assert trace.error_count == 0

    def test_add_multiple_spans(self):
        """添加多个span应该正常工作"""
        trace = AgentTrace(agent_id="test-agent")
        for i in range(100):
            trace.add_span(TraceSpan(
                trace_id=trace.trace_id,
                name=f"span-{i}",
            ))
        assert trace.span_count == 100

    def test_span_error_counting(self):
        """错误计数应该正常工作"""
        from behavior_core.models.agent_trace import SpanStatus
        trace = AgentTrace(agent_id="test-agent")
        trace.add_span(TraceSpan(
            trace_id=trace.trace_id,
            name="ok-span",
            status=SpanStatus.OK,
        ))
        trace.add_span(TraceSpan(
            trace_id=trace.trace_id,
            name="error-span",
            status=SpanStatus.ERROR,
        ))
        assert trace.error_count == 1

    def test_get_nonexistent_span(self):
        """获取不存在的span应该返回None"""
        trace = AgentTrace(agent_id="test-agent")
        assert trace.get_span("nonexistent") is None
