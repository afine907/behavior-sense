"""
Agent画像模型
"""
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class AgentStatus(str, Enum):
    """Agent状态"""
    ACTIVE = "active"
    IDLE = "idle"
    PAUSED = "paused"
    ERROR = "error"
    TERMINATED = "terminated"
    DEPRECATED = "deprecated"


class SafetyRating(str, Enum):
    """安全评级"""
    TRUSTED = "trusted"        # 完全信任
    STANDARD = "standard"      # 标准权限
    RESTRICTED = "restricted"  # 受限权限
    QUARANTINED = "quarantined"  # 隔离中
    BLOCKED = "blocked"        # 已封禁


class CostTier(str, Enum):
    """成本等级"""
    FREE = "free"          # 免费额度
    BASIC = "basic"        # 基础配额
    STANDARD = "standard"  # 标准配额
    PREMIUM = "premium"    # 高级配额
    UNLIMITED = "unlimited"  # 无限制


class AgentProfile(BaseModel):
    """Agent画像模型 - 替代UserProfile"""
    model_config = ConfigDict(use_enum_values=True)

    agent_id: str
    agent_name: str | None = None
    agent_type: str | None = None  # matches AgentType enum
    description: str | None = None

    # Identity
    model_name: str | None = None  # e.g., "gpt-4", "claude-3-opus"
    model_version: str | None = None
    framework: str | None = None  # e.g., "langchain", "autogen", "crewai"
    owner: str | None = None
    organization: str | None = None
    purpose: str | None = None  # what this agent is designed to do

    # Status
    status: AgentStatus = AgentStatus.ACTIVE
    safety_rating: SafetyRating = SafetyRating.STANDARD
    cost_tier: CostTier = CostTier.STANDARD

    # Capabilities
    capabilities: list[str] = Field(default_factory=list)
    supported_tools: list[str] = Field(default_factory=list)
    max_context_window: int | None = None

    # Tags (similar to UserTags concept)
    behavior_tags: list[str] = Field(default_factory=list)
    performance_tags: list[str] = Field(default_factory=list)
    safety_tags: list[str] = Field(default_factory=list)
    custom_tags: dict[str, Any] = Field(default_factory=dict)

    # Risk assessment
    risk_score: float = 0.0  # 0.0-1.0
    risk_factors: list[str] = Field(default_factory=list)

    # Metadata
    create_time: datetime = Field(default_factory=_utc_now)
    update_time: datetime = Field(default_factory=_utc_now)
    first_seen: datetime = Field(default_factory=_utc_now)
    last_active: datetime = Field(default_factory=_utc_now)


class AgentStat(BaseModel):
    """Agent统计模型 - 替代UserStat"""
    model_config = ConfigDict(use_enum_values=True)

    agent_id: str

    # 基础统计
    total_events: int = 0
    total_sessions: int = 0
    total_tasks: int = 0
    total_tool_calls: int = 0
    total_llm_calls: int = 0
    total_delegations: int = 0

    # Token统计
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cached_tokens: int = 0

    # 成本统计
    total_cost_usd: float = 0.0

    # 时间窗口统计 - 事件
    events_1h: int = 0
    events_1d: int = 0
    events_7d: int = 0
    events_30d: int = 0

    # 时间窗口统计 - Token
    tokens_1h: int = 0
    tokens_1d: int = 0
    tokens_7d: int = 0
    tokens_30d: int = 0

    # 时间窗口统计 - 成本
    cost_1h: float = 0.0
    cost_1d: float = 0.0
    cost_7d: float = 0.0
    cost_30d: float = 0.0

    # 时间窗口统计 - 任务
    tasks_1d: int = 0
    tasks_7d: int = 0
    tasks_30d: int = 0

    # 性能统计
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    success_rate: float = 0.0
    error_rate: float = 0.0
    timeout_rate: float = 0.0

    # 最近活动
    last_event_time: datetime | None = None
    last_tool_call_time: datetime | None = None
    last_llm_call_time: datetime | None = None
    last_error_time: datetime | None = None
    last_task_completion_time: datetime | None = None

    update_time: datetime = Field(default_factory=_utc_now)


class AgentComparison(BaseModel):
    """Agent对比分析模型"""
    agent_ids: list[str]
    comparison_time: datetime = Field(default_factory=_utc_now)

    # Per-agent metrics
    metrics: dict[str, dict[str, float]] = Field(default_factory=dict)
    # e.g., {"agent_1": {"success_rate": 0.95, "avg_latency": 150, ...}}

    # Rankings
    rankings: dict[str, list[str]] = Field(default_factory=dict)
    # e.g., {"success_rate": ["agent_1", "agent_2"], "cost_efficiency": [...]}

    # Insights
    insights: list[str] = Field(default_factory=list)
