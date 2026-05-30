"""
Agent执行追踪模型
"""
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class SpanStatus(str, Enum):
    """Span状态"""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class SpanKind(str, Enum):
    """Span类型"""
    AGENT = "agent"
    LLM = "llm"
    TOOL = "tool"
    CHAIN = "chain"
    RETRIEVER = "retriever"
    PARSER = "parser"


class TraceSpan(BaseModel):
    """追踪Span - OpenTelemetry风格"""
    model_config = ConfigDict(use_enum_values=True)

    span_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:16])
    trace_id: str
    parent_span_id: str | None = None
    name: str
    kind: SpanKind = SpanKind.AGENT

    # Timing
    start_time: datetime = Field(default_factory=_utc_now)
    end_time: datetime | None = None

    # Context
    agent_id: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)

    # Status
    status: SpanStatus = SpanStatus.OK
    status_message: str | None = None

    # Events (logs within the span)
    events: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def duration_ms(self) -> float | None:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None


class AgentTrace(BaseModel):
    """Agent执行追踪 - 完整的执行DAG"""
    model_config = ConfigDict(use_enum_values=True)

    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    session_id: str | None = None
    task_id: str | None = None

    # Root span
    root_span_id: str | None = None

    # All spans in this trace
    spans: list[TraceSpan] = Field(default_factory=list)

    # Trace-level metadata
    start_time: datetime = Field(default_factory=_utc_now)
    end_time: datetime | None = None
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    # Error info
    error_count: int = 0
    has_timeout: bool = False

    @property
    def duration_ms(self) -> float | None:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None

    @property
    def span_count(self) -> int:
        return len(self.spans)

    def add_span(self, span: TraceSpan) -> None:
        """添加span到trace"""
        self.spans.append(span)
        if span.status == SpanStatus.ERROR:
            self.error_count += 1
        if span.status == SpanStatus.TIMEOUT:
            self.has_timeout = True

    def get_span(self, span_id: str) -> TraceSpan | None:
        """获取指定span"""
        for span in self.spans:
            if span.span_id == span_id:
                return span
        return None

    def get_children(self, parent_span_id: str) -> list[TraceSpan]:
        """获取子spans"""
        return [s for s in self.spans if s.parent_span_id == parent_span_id]
