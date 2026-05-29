"""
AI Agent 行为事件模型

替代人类行为事件模型 (event.py)，专注于 AI Agent 的行为追踪，
包括工具调用、LLM 请求、内存操作、任务委派等。
"""
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _utc_now() -> datetime:
    """获取当前 UTC 时间"""
    return datetime.now(UTC)


class AgentEventType(str, Enum):
    """Agent 事件类型枚举"""

    # 工具相关
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"

    # LLM 交互
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"

    # 记忆操作
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"

    # 计划管理
    PLAN_CREATE = "plan_create"
    PLAN_UPDATE = "plan_update"

    # 协作与委派
    DELEGATION = "delegation"

    # 异常处理
    ERROR = "error"
    RETRY = "retry"
    TIMEOUT = "timeout"

    # 安全与合规
    GUARDRAIL_TRIGGER = "guardrail_trigger"
    COST_ALERT = "cost_alert"

    # 会话生命周期
    SESSION_START = "session_start"
    SESSION_END = "session_end"


class AgentType(str, Enum):
    """AI Agent 类型枚举"""

    LLM_AGENT = "llm_agent"
    TOOL_AGENT = "tool_agent"
    WORKFLOW_AGENT = "workflow_agent"
    MULTI_AGENT = "multi_agent"
    AUTONOMOUS = "autonomous"
    HUMAN_IN_LOOP = "human_in_loop"


class TokenUsage(BaseModel):
    """Token 用量模型 — 记录 LLM 请求的 token 消耗详情"""

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    prompt_tokens: int = Field(
        default=0, ge=0, description="Number of tokens in the prompt (input)"
    )
    completion_tokens: int = Field(
        default=0, ge=0, description="Number of tokens in the completion (output)"
    )
    total_tokens: int = Field(
        default=0, ge=0, description="Total tokens consumed (prompt + completion)"
    )
    cache_hit_tokens: int = Field(
        default=0, ge=0, description="Number of tokens served from cache"
    )
    cache_miss_tokens: int = Field(
        default=0, ge=0, description="Number of tokens that missed cache"
    )

    @model_validator(mode="after")
    def compute_total_and_validate_cache(self) -> "TokenUsage":
        """Auto-compute total_tokens and validate cache token bounds."""
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens
        if self.cache_hit_tokens > self.prompt_tokens:
            raise ValueError(
                f"cache_hit_tokens ({self.cache_hit_tokens}) cannot exceed "
                f"prompt_tokens ({self.prompt_tokens})"
            )
        if self.cache_miss_tokens > self.prompt_tokens:
            raise ValueError(
                f"cache_miss_tokens ({self.cache_miss_tokens}) cannot exceed "
                f"prompt_tokens ({self.prompt_tokens})"
            )
        if self.cache_hit_tokens + self.cache_miss_tokens > self.prompt_tokens > 0:
            raise ValueError(
                f"Sum of cache_hit_tokens ({self.cache_hit_tokens}) and "
                f"cache_miss_tokens ({self.cache_miss_tokens}) cannot exceed "
                f"prompt_tokens ({self.prompt_tokens})"
            )
        return self


class ToolCall(BaseModel):
    """工具调用模型 — 记录单次工具调用的输入、输出与结果"""

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    tool_name: str = Field(
        ..., min_length=1, max_length=256, description="Name of the tool being called"
    )
    tool_input: dict[str, Any] = Field(
        default_factory=dict, description="Input parameters passed to the tool"
    )
    tool_output: dict[str, Any] | None = Field(
        default=None, description="Output returned by the tool (None if not yet completed)"
    )
    tool_version: str | None = Field(
        default=None, max_length=64, description="Version identifier of the tool"
    )
    duration_ms: float | None = Field(
        default=None, ge=0, description="Execution duration in milliseconds (non-negative)"
    )
    success: bool | None = Field(
        default=None, description="Whether the tool call succeeded (None if pending)"
    )

    @field_validator("tool_name")
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        """Ensure tool_name is not blank after stripping whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("tool_name must not be blank or whitespace-only")
        return stripped


class AgentBehavior(BaseModel):
    """Agent 行为事件模型 — 替代 UserBehavior，记录 AI Agent 的每一次行为"""

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        min_length=1,
        max_length=128,
        description="Unique event identifier (auto-generated UUID if not provided)",
    )
    agent_id: str = Field(
        ..., min_length=1, max_length=128, description="Unique agent identifier"
    )
    agent_type: AgentType = Field(..., description="Classification of the AI agent")
    event_type: AgentEventType = Field(..., description="Type of agent behavior event")
    timestamp: datetime = Field(
        default_factory=_utc_now, description="UTC timestamp when the event occurred"
    )

    # 链路追踪 (OpenTelemetry 风格)
    trace_id: str | None = Field(
        default=None, max_length=128, description="Distributed trace identifier"
    )
    parent_span_id: str | None = Field(
        default=None, max_length=128, description="Parent span identifier in the trace"
    )

    # 会话与任务
    session_id: str | None = Field(
        default=None, max_length=128, description="Session grouping identifier"
    )
    task_id: str | None = Field(
        default=None, max_length=128, description="Task or workflow identifier"
    )

    # 模型信息
    model_name: str | None = Field(
        default=None, max_length=256, description="Name of the LLM model used"
    )
    model_version: str | None = Field(
        default=None, max_length=128, description="Version of the LLM model used"
    )

    # 业务属性
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary key-value business properties"
    )

    # 结构化数据 (前向引用)
    token_usage: "TokenUsage | None" = Field(
        default=None, description="Token consumption details for LLM events"
    )
    tool_call: "ToolCall | None" = Field(
        default=None, description="Tool call details for tool-related events"
    )

    # 性能与结果
    latency_ms: float | None = Field(
        default=None, ge=0, description="Event processing latency in milliseconds"
    )
    success: bool | None = Field(
        default=None, description="Whether the event completed successfully"
    )

    # 错误信息
    error_type: str | None = Field(
        default=None, max_length=256, description="Error classification (e.g., TimeoutError)"
    )
    error_message: str | None = Field(
        default=None, max_length=4096, description="Human-readable error description"
    )

    # 成本追踪
    cost_usd: float | None = Field(
        default=None, ge=0, description="Estimated cost in USD for this event"
    )

    @field_validator("agent_id")
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        """Ensure agent_id is not blank after stripping whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("agent_id must not be blank or whitespace-only")
        return stripped

    @field_validator("error_type", "error_message")
    @classmethod
    def normalize_error_fields(cls, v: str | None) -> str | None:
        """Convert empty strings to None for error fields."""
        if v is not None and not v.strip():
            return None
        return v

    @field_validator("model_name", "model_version")
    @classmethod
    def normalize_optional_strings(cls, v: str | None) -> str | None:
        """Convert empty strings to None for optional string fields."""
        if v is not None and not v.strip():
            return None
        return v

    @model_validator(mode="after")
    def validate_error_consistency(self) -> "AgentBehavior":
        """Ensure error fields are consistent: error_message requires error_type."""
        if self.error_message and not self.error_type:
            raise ValueError(
                "error_type must be provided when error_message is set; "
                "an error message without a classification is ambiguous"
            )
        return self


class StandardAgentEvent(BaseModel):
    """标准化 Agent 事件模型 — 替代 StandardEvent，用于下游存储与分析"""

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    event_id: str = Field(
        ..., min_length=1, max_length=128, description="Unique event identifier"
    )
    agent_id: str = Field(
        ..., min_length=1, max_length=128, description="Unique agent identifier"
    )
    agent_type: str = Field(
        ..., min_length=1, max_length=64, description="Classification of the AI agent"
    )
    event_type: str = Field(
        ..., min_length=1, max_length=64, description="Type of agent behavior event"
    )
    timestamp: datetime = Field(..., description="UTC timestamp when the event occurred")
    processed_at: datetime = Field(
        default_factory=_utc_now, description="UTC timestamp when the event was processed"
    )

    # 链路与会话
    trace_id: str | None = Field(
        default=None, max_length=128, description="Distributed trace identifier"
    )
    session_id: str | None = Field(
        default=None, max_length=128, description="Session grouping identifier"
    )
    task_id: str | None = Field(
        default=None, max_length=128, description="Task or workflow identifier"
    )

    # 业务属性
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary key-value business properties"
    )
    tags: list[str] = Field(
        default_factory=list, description="Classification tags for filtering and analysis"
    )

    # 上下文信息
    agent_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent metadata, including model name, version, and capabilities",
    )
    cost_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Cost context, including token usage, fees, and cache hit ratio",
    )
    safety_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Safety context, including guardrail triggers and risk scores",
    )

    @field_validator("event_id", "agent_id")
    @classmethod
    def validate_id_fields(cls, v: str) -> str:
        """Ensure ID fields are not blank after stripping whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("ID fields must not be blank or whitespace-only")
        return stripped

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Strip whitespace from tags and remove duplicates while preserving order."""
        seen: set[str] = set()
        result: list[str] = []
        for tag in v:
            stripped = tag.strip()
            if stripped and stripped not in seen:
                seen.add(stripped)
                result.append(stripped)
        return result

    @model_validator(mode="after")
    def validate_timestamp_order(self) -> "StandardAgentEvent":
        """Ensure processed_at is not before the event timestamp."""
        if self.processed_at < self.timestamp:
            raise ValueError(
                f"processed_at ({self.processed_at.isoformat()}) cannot be before "
                f"timestamp ({self.timestamp.isoformat()})"
            )
        return self
