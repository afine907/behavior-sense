"""
AI Agent 行为事件模型

替代人类行为事件模型 (event.py)，专注于 AI Agent 的行为追踪，
包括工具调用、LLM 请求、内存操作、任务委派等。
"""
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
    """Token 用量模型"""

    model_config = ConfigDict(use_enum_values=True)

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cache_hit_tokens: int = 0
    cache_miss_tokens: int = 0


class ToolCall(BaseModel):
    """工具调用模型"""

    model_config = ConfigDict(use_enum_values=True)

    tool_name: str
    tool_input: dict[str, Any] = Field(default_factory=dict)
    tool_output: dict[str, Any] | None = None
    tool_version: str | None = None
    duration_ms: float | None = None
    success: bool | None = None


class AgentBehavior(BaseModel):
    """Agent 行为事件模型 — 替代 UserBehavior"""

    model_config = ConfigDict(use_enum_values=True)

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    agent_type: AgentType
    event_type: AgentEventType
    timestamp: datetime = Field(default_factory=_utc_now)

    # 链路追踪 (OpenTelemetry 风格)
    trace_id: str | None = None
    parent_span_id: str | None = None

    # 会话与任务
    session_id: str | None = None
    task_id: str | None = None

    # 模型信息
    model_name: str | None = None
    model_version: str | None = None

    # 业务属性
    properties: dict[str, Any] = Field(default_factory=dict)

    # 结构化数据 (前向引用)
    token_usage: "TokenUsage | None" = None
    tool_call: "ToolCall | None" = None

    # 性能与结果
    latency_ms: float | None = None
    success: bool | None = None

    # 错误信息
    error_type: str | None = None
    error_message: str | None = None

    # 成本追踪
    cost_usd: float | None = None


class StandardAgentEvent(BaseModel):
    """标准化 Agent 事件模型 — 替代 StandardEvent"""

    model_config = ConfigDict(use_enum_values=True)

    event_id: str
    agent_id: str
    agent_type: str
    event_type: str
    timestamp: datetime
    processed_at: datetime = Field(default_factory=_utc_now)

    # 链路与会话
    trace_id: str | None = None
    session_id: str | None = None
    task_id: str | None = None

    # 业务属性
    properties: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    # 上下文信息
    agent_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent 元数据，如模型名称、版本、能力等",
    )
    cost_context: dict[str, Any] = Field(
        default_factory=dict,
        description="成本上下文，包括 token 用量、费用、缓存命中率等",
    )
    safety_context: dict[str, Any] = Field(
        default_factory=dict,
        description="安全上下文，包括 guardrail 触发、风险评分等",
    )
