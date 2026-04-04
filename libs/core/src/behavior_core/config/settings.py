"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from pydantic import SecretStr, field_validator
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    app_name: str = "behavior-sense"
    app_env: Literal["development", "testing", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Pulsar 配置
    pulsar_url: str = "pulsar://localhost:6650"
    pulsar_admin_url: str = "http://localhost:8080"
    pulsar_tenant: str = "behavior-sense"
    pulsar_namespace: str = "default"

    # PostgreSQL 配置
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: SecretStr = SecretStr("")  # 必须从环境变量获取
    postgres_db: str = "behavior_sense"
    postgres_pool_size: int = 10
    postgres_max_overflow: int = 20

    # Redis 配置
    redis_url: str = "redis://localhost:6379"
    redis_password: SecretStr = SecretStr("")  # 可选，从环境变量获取
    redis_max_connections: int = 100

    # ClickHouse 配置
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 9000
    clickhouse_user: str = "default"
    clickhouse_password: SecretStr = SecretStr("")
    clickhouse_database: str = "behavior_sense"

    # Elasticsearch 配置
    es_host: str = "localhost"
    es_port: int = 9200
    es_user: str = ""
    es_password: SecretStr = SecretStr("")

    # JWT 配置
    jwt_secret_key: SecretStr = SecretStr("change-this-secret-key-in-production")  # 必须通过环境变量设置
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    jwt_issuer: str = "behavior-sense"

    # CORS 配置
    cors_origins: str = ""  # 逗号分隔的允许域名列表

    # 服务端口配置
    mock_port: int = 8001
    rules_port: int = 8002
    insight_port: int = 8003
    audit_port: int = 8004

    @field_validator("postgres_password", "clickhouse_password", "es_password", "redis_password", mode="before")
    @classmethod
    def validate_password(cls, v):
        """验证密码不为空（生产环境）"""
        if isinstance(v, str):
            return SecretStr(v)
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def database_url(self) -> str:
        """异步数据库连接URL"""
        password = self.postgres_password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        """同步数据库连接URL"""
        password = self.postgres_password.get_secret_value()
        return (
            f"postgresql://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def pulsar_topic_base(self) -> str:
        """Pulsar Topic 基础路径"""
        return f"persistent://{self.pulsar_tenant}/{self.pulsar_namespace}"

    def pulsar_topic(self, name: str) -> str:
        """获取完整 Pulsar Topic 路径"""
        return f"{self.pulsar_topic_base}/{name}"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 便捷访问
settings = get_settings()
