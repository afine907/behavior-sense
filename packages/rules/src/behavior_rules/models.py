"""
规则模型定义

定义规则引擎所需的数据模型，包括规则条件、动作和匹配结果。
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ActionType(str, Enum):
    """动作类型枚举"""
    TAG_USER = "TAG_USER"
    TRIGGER_AUDIT = "TRIGGER_AUDIT"
    SEND_NOTIFICATION = "SEND_NOTIFICATION"
    BLOCK_USER = "BLOCK_USER"
    ALERT = "ALERT"


def _utc_now() -> datetime:
    """获取当前 UTC 时间"""
    return datetime.now(timezone.utc)


class RuleCondition(BaseModel):
    """规则条件模型"""
    field: str  # 字段名，如 event_count, total_amount
    operator: str  # 操作符：>, >=, <, <=, ==, !=, in, not_in, contains
    value: Any  # 比较值

    def to_expression(self) -> str:
        """将条件转换为 Python 表达式"""
        if self.operator == ">":
            return f"{self.field} > {repr(self.value)}"
        elif self.operator == ">=":
            return f"{self.field} >= {repr(self.value)}"
        elif self.operator == "<":
            return f"{self.field} < {repr(self.value)}"
        elif self.operator == "<=":
            return f"{self.field} <= {repr(self.value)}"
        elif self.operator == "==":
            return f"{self.field} == {repr(self.value)}"
        elif self.operator == "!=":
            return f"{self.field} != {repr(self.value)}"
        elif self.operator == "in":
            return f"{self.field} in {repr(self.value)}"
        elif self.operator == "not_in":
            return f"{self.field} not in {repr(self.value)}"
        elif self.operator == "contains":
            return f"{repr(self.value)} in {self.field}"
        else:
            raise ValueError(f"Unsupported operator: {self.operator}")


class RuleAction(BaseModel):
    """规则动作模型"""
    type: ActionType
    params: dict[str, Any] = Field(default_factory=dict)
    async_exec: bool = True  # 是否异步执行
    retry_count: int = 3  # 重试次数
    retry_delay: float = 1.0  # 重试延迟（秒）


class Rule(BaseModel):
    """规则定义模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str | None = None
    condition: str  # Python 表达式，如 "purchase_count >= 5 and total_amount > 1000"
    priority: int = 0  # 优先级，数值越大优先级越高
    enabled: bool = True
    actions: list[RuleAction] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)  # 规则标签，用于分类
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    created_by: str | None = None
    version: int = 1


class RuleCreate(BaseModel):
    """创建规则请求模型"""
    name: str
    description: str | None = None
    condition: str
    priority: int = 0
    enabled: bool = True
    actions: list[RuleAction] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class RuleUpdate(BaseModel):
    """更新规则请求模型"""
    name: str | None = None
    description: str | None = None
    condition: str | None = None
    priority: int | None = None
    enabled: bool | None = None
    actions: list[RuleAction] | None = None
    tags: list[str] | None = None


class RuleMatchResult(BaseModel):
    """规则匹配结果模型"""
    rule_id: str
    rule_name: str
    matched: bool
    context: dict[str, Any] = Field(default_factory=dict)
    actions_executed: list[dict[str, Any]] = Field(default_factory=list)
    executed_at: datetime = Field(default_factory=_utc_now)
    execution_time_ms: float = 0.0  # 执行耗时（毫秒）
    error: str | None = None


class EvaluateRequest(BaseModel):
    """评估请求模型"""
    context: dict[str, Any]  # 评估上下文，包含 user_id, event_count 等变量
    rule_ids: list[str] | None = None  # 指定评估的规则ID，为空则评估所有
    execute_actions: bool = True  # 是否执行动作


class EvaluateResponse(BaseModel):
    """评估响应模型"""
    matched_rules: list[RuleMatchResult]
    total_rules_evaluated: int
    execution_time_ms: float
