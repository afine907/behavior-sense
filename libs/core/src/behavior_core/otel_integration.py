"""
OpenTelemetry集成 - 使BehaviorSense兼容OTel生态
"""
import time
from datetime import UTC, datetime
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.resources import Resource

from behavior_core.models.agent_event import AgentBehavior, AgentEventType


class BehaviorSenseTracer:
    """BehaviorSense OpenTelemetry追踪器"""

    def __init__(self, service_name: str = "behaviorsense"):
        self.service_name = service_name
        self._provider: TracerProvider | None = None
        self._tracer: trace.Tracer | None = None

    def initialize(
        self,
        endpoint: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """初始化OTel追踪器"""
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": "2.0.0",
        })

        self._provider = TracerProvider(resource=resource)

        if endpoint:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers or {})
        else:
            exporter = ConsoleSpanExporter()

        self._provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(self._provider)
        self._tracer = trace.get_tracer(self.service_name)

    def get_tracer(self) -> trace.Tracer:
        """获取追踪器"""
        if not self._tracer:
            self.initialize()
        return self._tracer

    def start_agent_span(
        self,
        event: AgentBehavior,
        parent_context: Any | None = None,
    ) -> trace.Span:
        """开始Agent事件Span"""
        tracer = self.get_tracer()

        span = tracer.start_span(
            name=f"{event.event_type}:{event.agent_id}",
            attributes={
                "agent.id": event.agent_id,
                "agent.type": event.agent_type,
                "event.type": event.event_type,
                "event.id": event.event_id,
                "model.name": event.model_name or "",
                "session.id": event.session_id or "",
                "trace.id": event.trace_id or "",
                "task.id": event.task_id or "",
            },
        )

        # Add token usage if present
        if event.token_usage:
            span.set_attribute("gen_ai.prompt_tokens", event.token_usage.prompt_tokens)
            span.set_attribute("gen_ai.completion_tokens", event.token_usage.completion_tokens)
            span.set_attribute("gen_ai.total_tokens", event.token_usage.total_tokens)
            span.set_attribute("gen_ai.cost_usd", event.token_usage.cost_usd)

        # Add tool call if present
        if event.tool_call:
            span.set_attribute("tool.name", event.tool_call.tool_name)
            span.set_attribute("tool.type", event.tool_call.tool_type)
            span.set_attribute("tool.latency_ms", event.tool_call.latency_ms)
            span.set_attribute("tool.success", event.tool_call.success)

        # Add latency
        if event.latency_ms:
            span.set_attribute("duration_ms", event.latency_ms)

        return span

    def end_agent_span(
        self,
        span: trace.Span,
        event: AgentBehavior,
    ) -> None:
        """结束Agent事件Span"""
        if event.success is False:
            span.set_status(Status(StatusCode.ERROR, event.error_message or "Unknown error"))
            if event.error_type:
                span.set_attribute("error.type", event.error_type)
            if event.error_message:
                span.set_attribute("error.message", event.error_message)
        else:
            span.set_status(Status(StatusCode.OK))

        span.end()

    def record_agent_event(self, event: AgentBehavior) -> None:
        """记录Agent事件到OTel"""
        span = self.start_agent_span(event)
        self.end_agent_span(span, event)


# GenAI Semantic Conventions
class GenAIAttributes:
    """GenAI语义约定属性"""

    # Model attributes
    GEN_AI_SYSTEM = "gen_ai.system"
    GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
    GEN_AI_REQUEST_MAX_TOKENS = "gen_ai.request.max_tokens"
    GEN_AI_REQUEST_TEMPERATURE = "gen_ai.request.temperature"

    # Response attributes
    GEN_AI_RESPONSE_MODEL = "gen_ai.response.model"
    GEN_AI_RESPONSE_FINISH_REASONS = "gen_ai.response.finish_reasons"

    # Token attributes
    GEN_AI_USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
    GEN_AI_USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
    GEN_AI_USAGE_TOTAL_TOKENS = "gen_ai.usage.total_tokens"

    # Cost attributes
    GEN_AI_USAGE_COST_USD = "gen_ai.usage.cost_usd"

    # Agent attributes
    AGENT_ID = "agent.id"
    AGENT_TYPE = "agent.type"
    AGENT_NAME = "agent.name"

    # Tool attributes
    TOOL_NAME = "tool.name"
    TOOL_TYPE = "tool.type"
    TOOL_LATENCY_MS = "tool.latency_ms"
    TOOL_SUCCESS = "tool.success"

    # Session attributes
    SESSION_ID = "session.id"
    TASK_ID = "task.id"
    TRACE_ID = "trace.id"


def create_span_from_agent_event(
    event: AgentBehavior,
    tracer: trace.Tracer | None = None,
) -> trace.Span:
    """从Agent事件创建OTel Span"""
    if tracer is None:
        tracer = trace.get_tracer("behaviorsense")

    attributes = {
        GenAIAttributes.AGENT_ID: event.agent_id,
        GenAIAttributes.AGENT_TYPE: event.agent_type,
        GenAIAttributes.TASK_ID: event.task_id or "",
        GenAIAttributes.SESSION_ID: event.session_id or "",
    }

    if event.model_name:
        attributes[GenAIAttributes.GEN_AI_REQUEST_MODEL] = event.model_name

    if event.token_usage:
        attributes[GenAIAttributes.GEN_AI_USAGE_INPUT_TOKENS] = event.token_usage.prompt_tokens
        attributes[GenAIAttributes.GEN_AI_USAGE_OUTPUT_TOKENS] = event.token_usage.completion_tokens
        attributes[GenAIAttributes.GEN_AI_USAGE_TOTAL_TOKENS] = event.token_usage.total_tokens
        attributes[GenAIAttributes.GEN_AI_USAGE_COST_USD] = event.token_usage.cost_usd

    if event.tool_call:
        attributes[GenAIAttributes.TOOL_NAME] = event.tool_call.tool_name
        attributes[GenAIAttributes.TOOL_TYPE] = event.tool_call.tool_type
        attributes[GenAIAttributes.TOOL_LATENCY_MS] = event.tool_call.latency_ms
        attributes[GenAIAttributes.TOOL_SUCCESS] = event.tool_call.success

    span = tracer.start_span(
        name=f"{event.event_type}:{event.agent_id}",
        attributes=attributes,
    )

    if event.success is False:
        span.set_status(Status(StatusCode.ERROR, event.error_message or "Unknown error"))

    return span
