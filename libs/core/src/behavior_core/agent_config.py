"""
Agent Analytics配置管理
"""
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """运行环境"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ClickHouseConfig(BaseModel):
    """ClickHouse配置"""
    url: str = "http://localhost:8123"
    database: str = "behaviorsense"
    username: str = "default"
    password: str = ""
    max_connections: int = Field(default=10, ge=1, le=100)
    connect_timeout: float = Field(default=10.0, gt=0)
    query_timeout: float = Field(default=30.0, gt=0)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("ClickHouse URL must start with http:// or https://")
        return v


class RedisConfig(BaseModel):
    """Redis配置"""
    url: str = "redis://localhost:6379"
    max_connections: int = Field(default=20, ge=1, le=200)
    socket_timeout: float = Field(default=5.0, gt=0)
    retry_on_timeout: bool = True
    decode_responses: bool = True

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("redis://", "rediss://")):
            raise ValueError("Redis URL must start with redis:// or rediss://")
        return v


class PulsarConfig(BaseModel):
    """Pulsar配置"""
    url: str = "pulsar://localhost:6650"
    topic_prefix: str = "behaviorsense"
    subscription_name: str = "agent-analytics"
    consumer_name: str = "agent-consumer"
    producer_name: str = "agent-producer"

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith("pulsar://"):
            raise ValueError("Pulsar URL must start with pulsar://")
        return v


class DatabaseConfig(BaseModel):
    """PostgreSQL配置"""
    url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/behaviorsense"
    pool_size: int = Field(default=10, ge=1, le=50)
    max_overflow: int = Field(default=20, ge=0, le=100)
    pool_timeout: float = Field(default=30.0, gt=0)
    pool_recycle: int = Field(default=3600, gt=0)
    echo: bool = False


class DetectionConfig(BaseModel):
    """异常检测配置"""
    loop_detection: dict[str, Any] = Field(default_factory=lambda: {
        "min_repetitions": 5,
        "window_seconds": 60,
        "enabled": True,
    })
    cost_spike: dict[str, Any] = Field(default_factory=lambda: {
        "cost_per_minute_threshold": 1.0,
        "cost_spike_ratio": 5.0,
        "window_seconds": 60,
        "enabled": True,
    })
    token_explosion: dict[str, Any] = Field(default_factory=lambda: {
        "max_prompt_tokens": 100000,
        "max_completion_tokens": 50000,
        "max_total_per_session": 1000000,
        "enabled": True,
    })
    tool_abuse: dict[str, Any] = Field(default_factory=lambda: {
        "calls_per_minute": 60,
        "dangerous_calls_per_minute": 10,
        "enabled": True,
    })
    timeout_cascade: dict[str, Any] = Field(default_factory=lambda: {
        "timeout_count_threshold": 3,
        "window_seconds": 300,
        "enabled": True,
    })


class CostConfig(BaseModel):
    """成本配置"""
    daily_budget: float = Field(default=100.0, ge=0)
    weekly_budget: float = Field(default=500.0, ge=0)
    monthly_budget: float = Field(default=2000.0, ge=0)
    alert_threshold_pct: float = Field(default=80.0, ge=0, le=100)
    auto_pause_on_budget_exceeded: bool = False

    @model_validator(mode="after")
    def validate_budgets(self) -> "CostConfig":
        if self.weekly_budget < self.daily_budget * 2:
            self.weekly_budget = self.daily_budget * 7
        if self.monthly_budget < self.weekly_budget * 2:
            self.monthly_budget = self.weekly_budget * 4
        return self


class NotificationConfig(BaseModel):
    """通知配置"""
    enabled: bool = True
    channels: list[str] = Field(default_factory=lambda: ["console"])
    webhook_url: str | None = None
    slack_webhook_url: str | None = None
    critical_only: bool = False

    @field_validator("webhook_url", "slack_webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: str | None) -> str | None:
        if v and not v.startswith("http"):
            raise ValueError("Webhook URL must start with http:// or https://")
        return v


class AgentAnalyticsConfig(BaseSettings):
    """Agent Analytics主配置"""
    model_config = {
        "env_prefix": "BS_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    # 环境
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO

    # 服务端口
    mock_port: int = Field(default=8001, ge=1024, le=65535)
    rules_port: int = Field(default=8002, ge=1024, le=65535)
    insight_port: int = Field(default=8003, ge=1024, le=65535)
    audit_port: int = Field(default=8004, ge=1024, le=65535)
    logs_port: int = Field(default=8005, ge=1024, le=65535)

    # 基础设施
    clickhouse: ClickHouseConfig = Field(default_factory=ClickHouseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    pulsar: PulsarConfig = Field(default_factory=PulsarConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    # 业务配置
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    cost: CostConfig = Field(default_factory=CostConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)

    # 功能开关
    enable_agent_analytics: bool = True
    enable_anomaly_detection: bool = True
    enable_cost_tracking: bool = True
    enable_compliance_checking: bool = True
    enable_websocket: bool = True

    @model_validator(mode="after")
    def validate_environment(self) -> "AgentAnalyticsConfig":
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                self.debug = False
            if self.log_level == LogLevel.DEBUG:
                self.log_level = LogLevel.INFO
        return self

    def get_service_url(self, service: str) -> str:
        """获取服务URL"""
        port_map = {
            "mock": self.mock_port,
            "rules": self.rules_port,
            "insight": self.insight_port,
            "audit": self.audit_port,
            "logs": self.logs_port,
        }
        port = port_map.get(service)
        if not port:
            raise ValueError(f"Unknown service: {service}")
        return f"http://localhost:{port}"


def load_config() -> AgentAnalyticsConfig:
    """加载配置"""
    return AgentAnalyticsConfig()


# 全局配置实例
_config: AgentAnalyticsConfig | None = None


def get_config() -> AgentAnalyticsConfig:
    """获取全局配置"""
    global _config
    if _config is None:
        _config = load_config()
    return _config
