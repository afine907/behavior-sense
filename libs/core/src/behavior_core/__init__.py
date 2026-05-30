"""
BehaviorSense 核心库
"""
from behavior_core.api_response import (
    ApiResponse,
    ErrorResponse,
    PaginatedResponse,
    forbidden,
    internal_error,
    not_found,
    rate_limit_exceeded,
    unauthorized,
    validation_error,
)
from behavior_core.config.settings import Settings, get_settings, settings
from behavior_core.error_handlers import register_error_handlers
from behavior_core.exceptions import (
    AgentNotFoundError,
    AuthenticationError,
    BehaviorSenseError,
    ConfigurationError,
    CostLimitExceededError,
    RateLimitError,
    RuleEvaluationError,
    StreamProcessingError,
    ValidationError,
)
from behavior_core.health import (
    ComponentHealth,
    HealthChecker,
    HealthReport,
    HealthStatus,
    check_clickhouse_available,
    check_disk_usage,
    check_http_endpoint,
    check_memory_usage,
    check_redis_available,
)
from behavior_core.metrics import (
    AgentMetrics,
    Counter,
    Gauge,
    Histogram,
    MetricsRegistry,
    get_metrics,
)
from behavior_core.models import (
    AggregationResult,
    AlertEvent,
    EventType,
    StandardEvent,
    TagSource,
    TagValue,
    UserBehavior,
    UserLevel,
    UserProfile,
    UserStat,
    UserStatus,
    UserTags,
)
from behavior_core.performance import (
    BatchProcessor,
    ConnectionPool,
    LRUCache,
    RateLimiter,
    Timer,
    memoize,
)
from behavior_core.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    RetryConfig,
    with_circuit_breaker,
    with_retry,
)
from behavior_core.agent_config import (
    AgentAnalyticsConfig,
    ClickHouseConfig,
    CostConfig,
    DatabaseConfig,
    DetectionConfig,
    Environment,
    LogLevel,
    NotificationConfig,
    PulsarConfig,
    RedisConfig,
    get_config,
    load_config,
)
from behavior_core.agent_logging import (
    AgentEventLogger,
    PerformanceLogger,
    get_agent_logger,
    get_service_logger,
    setup_logging,
)

__all__ = [
    # 事件模型
    "EventType",
    "UserBehavior",
    "StandardEvent",
    "AggregationResult",
    "AlertEvent",
    # 用户模型
    "UserStatus",
    "UserLevel",
    "TagSource",
    "TagValue",
    "UserTags",
    "UserProfile",
    "UserStat",
    # 配置
    "Settings",
    "get_settings",
    "settings",
    # API响应
    "ApiResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "not_found",
    "validation_error",
    "unauthorized",
    "forbidden",
    "rate_limit_exceeded",
    "internal_error",
    # 错误处理
    "register_error_handlers",
    # 异常
    "BehaviorSenseError",
    "AgentNotFoundError",
    "ValidationError",
    "CostLimitExceededError",
    "RuleEvaluationError",
    "StreamProcessingError",
    "ConfigurationError",
    "AuthenticationError",
    "RateLimitError",
    # 健康检查
    "HealthStatus",
    "ComponentHealth",
    "HealthReport",
    "HealthChecker",
    "check_http_endpoint",
    "check_redis_available",
    "check_clickhouse_available",
    "check_memory_usage",
    "check_disk_usage",
    # 指标
    "Counter",
    "Gauge",
    "Histogram",
    "MetricsRegistry",
    "get_metrics",
    "AgentMetrics",
    # 性能
    "LRUCache",
    "BatchProcessor",
    "memoize",
    "RateLimiter",
    "ConnectionPool",
    "Timer",
    # 弹性模式
    "RetryConfig",
    "CircuitBreakerConfig",
    "CircuitState",
    "CircuitBreaker",
    "CircuitOpenError",
    "with_retry",
    "with_circuit_breaker",
    # Agent配置
    "Environment",
    "LogLevel",
    "ClickHouseConfig",
    "RedisConfig",
    "PulsarConfig",
    "DatabaseConfig",
    "DetectionConfig",
    "CostConfig",
    "NotificationConfig",
    "AgentAnalyticsConfig",
    "load_config",
    "get_config",
    # 日志
    "setup_logging",
    "get_agent_logger",
    "get_service_logger",
    "AgentEventLogger",
    "PerformanceLogger",
]
