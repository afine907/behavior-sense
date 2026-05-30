"""
Agent能力模型
"""
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class CapabilityLevel(str, Enum):
    """能力等级"""
    NOVICE = "novice"         # 初学者 - 经常失败
    INTERMEDIATE = "intermediate"  # 中级 - 偶尔失败
    ADVANCED = "advanced"     # 高级 - 很少失败
    EXPERT = "expert"         # 专家 - 几乎不失败


class CapabilityCategory(str, Enum):
    """能力类别"""
    REASONING = "reasoning"           # 推理能力
    TOOL_USE = "tool_use"             # 工具使用
    CODE_GENERATION = "code_generation"  # 代码生成
    DATA_ANALYSIS = "data_analysis"   # 数据分析
    COMMUNICATION = "communication"   # 交流能力
    PLANNING = "planning"             # 规划能力
    RESEARCH = "research"             # 研究能力
    CREATIVE = "creative"             # 创造力
    DOMAIN_SPECIFIC = "domain_specific"  # 领域特定


class AgentCapability(BaseModel):
    """Agent能力评估模型"""
    model_config = ConfigDict(use_enum_values=True)

    agent_id: str
    capability_name: str
    category: CapabilityCategory
    level: CapabilityLevel = CapabilityLevel.NOVICE

    # Performance metrics
    success_rate: float = 0.0      # 0.0-1.0
    avg_latency_ms: float = 0.0
    total_invocations: int = 0
    successful_invocations: int = 0
    failed_invocations: int = 0

    # Quality metrics
    avg_output_quality: float = 0.0  # 0.0-1.0 (human or auto-evaluated)
    consistency_score: float = 0.0   # 0.0-1.0 (output consistency)

    # Context
    supported_tools: list[str] = Field(default_factory=list)
    supported_models: list[str] = Field(default_factory=list)
    max_complexity: str = "low"  # low, medium, high, very_high

    # Timing
    first_seen: datetime = Field(default_factory=_utc_now)
    last_used: datetime = Field(default_factory=_utc_now)
    last_evaluated: datetime = Field(default_factory=_utc_now)

    # Trends
    improvement_rate: float = 0.0  # positive = improving, negative = degrading
    trend_period_days: int = 7

    def update_stats(self, success: bool, latency_ms: float, quality: float | None = None) -> None:
        """Update capability statistics after an invocation"""
        self.total_invocations += 1
        if success:
            self.successful_invocations += 1
        else:
            self.failed_invocations += 1

        # Running average for success rate
        self.success_rate = self.successful_invocations / self.total_invocations

        # Running average for latency
        if self.avg_latency_ms == 0:
            self.avg_latency_ms = latency_ms
        else:
            self.avg_latency_ms = (self.avg_latency_ms * 0.9) + (latency_ms * 0.1)

        # Update quality if provided
        if quality is not None:
            if self.avg_output_quality == 0:
                self.avg_output_quality = quality
            else:
                self.avg_output_quality = (self.avg_output_quality * 0.9) + (quality * 0.1)

        # Update level based on success rate
        if self.success_rate >= 0.95 and self.total_invocations >= 100:
            self.level = CapabilityLevel.EXPERT
        elif self.success_rate >= 0.85 and self.total_invocations >= 50:
            self.level = CapabilityLevel.ADVANCED
        elif self.success_rate >= 0.70 and self.total_invocations >= 20:
            self.level = CapabilityLevel.INTERMEDIATE
        else:
            self.level = CapabilityLevel.NOVICE

        self.last_used = _utc_now()


class AgentCapabilityMap(BaseModel):
    """Agent能力图谱 - 汇总Agent的所有能力"""
    model_config = ConfigDict(use_enum_values=True)

    agent_id: str
    capabilities: dict[str, AgentCapability] = Field(default_factory=dict)
    overall_score: float = 0.0  # 0.0-1.0 weighted average
    last_updated: datetime = Field(default_factory=_utc_now)

    def add_capability(self, capability: AgentCapability) -> None:
        self.capabilities[capability.capability_name] = capability
        self._recalculate_score()

    def get_capability(self, name: str) -> AgentCapability | None:
        return self.capabilities.get(name)

    def _recalculate_score(self) -> None:
        if not self.capabilities:
            self.overall_score = 0.0
            return
        scores = [c.success_rate for c in self.capabilities.values()]
        self.overall_score = sum(scores) / len(scores)
        self.last_updated = _utc_now()
