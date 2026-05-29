"""
SDK数据模型
"""
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class TokenUsage(BaseModel):
    """Token使用"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0
    model_name: str | None = None
    cost_usd: float = 0.0


class ToolCall(BaseModel):
    """工具调用"""
    tool_name: str
    tool_type: str = "custom"
    latency_ms: float = 0.0
    success: bool = True
    error_message: str | None = None


class AgentEvent(BaseModel):
    """Agent事件"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    agent_type: str = "llm_agent"
    event_type: str
    timestamp: datetime = Field(default_factory=_utc_now)
    trace_id: str | None = None
    session_id: str | None = None
    task_id: str | None = None
    model_name: str | None = None
    token_usage: TokenUsage | None = None
    tool_call: ToolCall | None = None
    latency_ms: float | None = None
    success: bool | None = None
    error_type: str | None = None
    error_message: str | None = None
    cost_usd: float | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class AgentProfile(BaseModel):
    """Agent画像"""
    agent_id: str
    agent_name: str | None = None
    agent_type: str | None = None
    model_name: str | None = None
    framework: str | None = None
    owner: str | None = None
    status: str = "active"
    safety_rating: str = "standard"
    cost_tier: str = "standard"
    capabilities: list[str] = Field(default_factory=list)
    risk_score: float = 0.0
