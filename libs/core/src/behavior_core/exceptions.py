"""
BehaviorSense 自定义异常
"""
from typing import Any


class BehaviorSenseError(Exception):
    """基础异常"""

    def __init__(
        self,
        message: str = "An error occurred",
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class AgentNotFoundError(BehaviorSenseError):
    """Agent未找到"""

    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent '{agent_id}' not found",
            details={"agent_id": agent_id},
        )


class ValidationError(BehaviorSenseError):
    """验证错误"""

    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"Validation failed for '{field}': {reason}",
            details={"field": field, "reason": reason},
        )


class CostLimitExceededError(BehaviorSenseError):
    """成本超限"""

    def __init__(self, agent_id: str, current_cost: float, limit: float):
        super().__init__(
            message=f"Cost limit exceeded for agent '{agent_id}': "
                    f"${current_cost:.2f} / ${limit:.2f}",
            details={
                "agent_id": agent_id,
                "current_cost": current_cost,
                "limit": limit,
            },
        )


class RuleEvaluationError(BehaviorSenseError):
    """规则评估错误"""

    def __init__(self, rule_id: str, reason: str):
        super().__init__(
            message=f"Rule evaluation failed for '{rule_id}': {reason}",
            details={"rule_id": rule_id, "reason": reason},
        )


class StreamProcessingError(BehaviorSenseError):
    """流处理错误"""

    def __init__(self, topic: str, reason: str):
        super().__init__(
            message=f"Stream processing error on topic '{topic}': {reason}",
            details={"topic": topic, "reason": reason},
        )


class ConfigurationError(BehaviorSenseError):
    """配置错误"""

    def __init__(self, key: str, reason: str):
        super().__init__(
            message=f"Configuration error for '{key}': {reason}",
            details={"key": key, "reason": reason},
        )


class AuthenticationError(BehaviorSenseError):
    """认证错误"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, details={"error_type": "authentication"})


class RateLimitError(BehaviorSenseError):
    """速率限制错误"""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message=f"Rate limit exceeded. Retry after {retry_after} seconds",
            details={"retry_after": retry_after},
        )
