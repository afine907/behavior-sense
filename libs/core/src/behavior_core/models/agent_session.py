"""
Agent会话/任务模型
"""
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class TaskStatus(str, Enum):
    """任务状态"""
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING = "waiting"  # waiting for human input or external event
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class AgentSession(BaseModel):
    """Agent会话/任务模型 - 替代简单的session_id"""
    model_config = ConfigDict(use_enum_values=True)

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    agent_type: str  # matches AgentType enum value
    task_id: str | None = None
    goal: str | None = None  # high-level goal description
    plan: list[str] = Field(default_factory=list)  # execution plan steps
    status: TaskStatus = TaskStatus.PLANNING
    priority: TaskPriority = TaskPriority.NORMAL

    # Execution context
    parent_session_id: str | None = None  # if delegated from another agent
    delegated_to: list[str] = Field(default_factory=list)  # sub-agent session IDs

    # Metrics
    total_events: int = 0
    total_tool_calls: int = 0
    total_llm_calls: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    # Timing
    start_time: datetime = Field(default_factory=_utc_now)
    end_time: datetime | None = None
    deadline: datetime | None = None

    # Result
    result_summary: str | None = None
    error_summary: str | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None

    @property
    def is_active(self) -> bool:
        return self.status in (TaskStatus.PLANNING, TaskStatus.EXECUTING, TaskStatus.WAITING)
