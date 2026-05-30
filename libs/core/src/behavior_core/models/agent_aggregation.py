"""
Agent聚合结果模型
"""
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class AgentAggregation(BaseModel):
    """Agent聚合结果 - 替代AggregationResult"""
    model_config = ConfigDict(use_enum_values=True)

    aggregation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    window_start: datetime
    window_end: datetime

    # Event counts by type
    event_count: int = 0
    tool_call_count: int = 0
    tool_result_count: int = 0
    llm_request_count: int = 0
    llm_response_count: int = 0
    error_count: int = 0
    timeout_count: int = 0
    delegation_count: int = 0

    # Token metrics
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0

    # Cost metrics
    total_cost_usd: float = 0.0

    # Performance metrics
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    max_latency_ms: float = 0.0

    # Quality metrics
    success_rate: float = 0.0
    error_rate: float = 0.0

    # Tool usage breakdown
    tool_usage: dict[str, int] = Field(default_factory=dict)  # tool_name -> count

    # Model usage breakdown
    model_usage: dict[str, int] = Field(default_factory=dict)  # model_name -> count

    # Session info
    unique_sessions: int = 0
    unique_tasks: int = 0

    # Anomaly indicators
    anomaly_score: float = 0.0  # 0.0-1.0
    anomaly_flags: list[str] = Field(default_factory=list)

    processed_at: datetime = Field(default_factory=_utc_now)


class CostBreakdown(BaseModel):
    """成本细分模型"""
    agent_id: str
    period_start: datetime
    period_end: datetime

    # By model
    cost_by_model: dict[str, float] = Field(default_factory=dict)
    tokens_by_model: dict[str, int] = Field(default_factory=dict)

    # By tool
    cost_by_tool: dict[str, float] = Field(default_factory=dict)
    calls_by_tool: dict[str, int] = Field(default_factory=dict)

    # By task
    cost_by_task: dict[str, float] = Field(default_factory=dict)

    # Totals
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    total_tool_calls: int = 0
    total_llm_calls: int = 0

    # Efficiency
    cost_per_success: float = 0.0
    tokens_per_success: int = 0


class PerformanceMetrics(BaseModel):
    """性能指标模型"""
    agent_id: str
    period_start: datetime
    period_end: datetime

    # Latency
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0

    # Throughput
    events_per_second: float = 0.0
    tool_calls_per_minute: float = 0.0
    llm_calls_per_minute: float = 0.0

    # Reliability
    success_rate: float = 0.0
    error_rate: float = 0.0
    timeout_rate: float = 0.0
    retry_rate: float = 0.0

    # Task completion
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_task_duration_ms: float = 0.0
