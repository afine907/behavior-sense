"""
Agent告警模型
"""
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class AgentAlertType(str, Enum):
    """Agent告警类型"""
    # Loop/Pattern anomalies
    DEAD_LOOP = "dead_loop"                  # Agent陷入死循环
    INFINITE_RETRY = "infinite_retry"        # 无限重试
    OSCILLATION = "oscillation"              # 行为振荡（反复做同一件事）

    # Cost anomalies
    COST_SPIKE = "cost_spike"                # 成本突然飙升
    BUDGET_EXCEEDED = "budget_exceeded"       # 超出预算
    TOKEN_EXPLOSION = "token_explosion"      # Token消耗爆炸

    # Security anomalies
    PROMPT_INJECTION = "prompt_injection"    # 检测到Prompt注入
    TOOL_ABUSE = "tool_abuse"                # 工具滥用
    DATA_EXFILTRATION = "data_exfiltration"  # 数据外泄尝试
    CAPABILITY_DRIFT = "capability_drift"    # 能力漂移（行为偏离预期）

    # Performance anomalies
    TIMEOUT_CASCADE = "timeout_cascade"      # 超时级联
    LATENCY_DEGRADATION = "latency_degradation"  # 延迟恶化
    ERROR_RATE_SPIKE = "error_rate_spike"    # 错误率飙升

    # Multi-agent anomalies
    RESOURCE_CONTENTION = "resource_contention"  # 多Agent资源竞争
    CASCADING_FAILURE = "cascading_failure"      # 级联失败
    DEADLOCK = "deadlock"                        # 多Agent死锁

    # Compliance
    POLICY_VIOLATION = "policy_violation"    # 策略违规
    UNAUTHORIZED_ACCESS = "unauthorized_access"  # 未授权访问


class AlertSeverity(str, Enum):
    """告警严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AutoAction(str, Enum):
    """自动处置动作"""
    NONE = "none"
    LOG = "log"
    THROTTLE = "throttle"      # 限流
    PAUSE = "pause"            # 暂停Agent
    KILL = "kill"              # 终止Agent
    ROLLBACK = "rollback"      # 回滚操作
    NOTIFY = "notify"          # 通知人工
    ESCALATE = "escalate"      # 升级处理


class AgentAlert(BaseModel):
    """Agent告警模型 - 替代AlertEvent"""
    model_config = ConfigDict(use_enum_values=True)

    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: AgentAlertType
    agent_id: str
    severity: AlertSeverity = AlertSeverity.MEDIUM
    message: str
    description: str | None = None

    # Context
    trace_id: str | None = None
    session_id: str | None = None
    task_id: str | None = None

    # Trigger details
    trigger_data: dict[str, Any] = Field(default_factory=dict)
    trigger_threshold: float | None = None
    trigger_value: float | None = None

    # Auto-action
    auto_action: AutoAction = AutoAction.NONE
    action_taken: bool = False
    action_result: str | None = None

    # Resolution
    resolved: bool = False
    resolved_by: str | None = None  # "auto" or human identifier
    resolved_at: datetime | None = None
    resolution_notes: str | None = None

    # Timing
    timestamp: datetime = Field(default_factory=_utc_now)
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    occurrence_count: int = 1

    # Escalation
    escalated: bool = False
    escalated_to: str | None = None
    escalated_at: datetime | None = None


class AlertRule(BaseModel):
    """告警规则定义"""
    model_config = ConfigDict(use_enum_values=True)

    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str | None = None
    alert_type: AgentAlertType
    severity: AlertSeverity = AlertSeverity.MEDIUM

    # Conditions
    metric: str  # e.g., "error_rate", "cost_per_hour", "avg_latency"
    operator: str  # ">", ">=", "<", "<=", "==", "!="
    threshold: float
    window_seconds: int = 60  # evaluation window

    # Actions
    auto_action: AutoAction = AutoAction.LOG
    notify_channels: list[str] = Field(default_factory=list)

    # Control
    enabled: bool = True
    cooldown_seconds: int = 300  # minimum time between alerts
    max_alerts_per_hour: int = 10

    # Scope
    agent_ids: list[str] = Field(default_factory=list)  # empty = all agents
    agent_types: list[str] = Field(default_factory=list)  # empty = all types
