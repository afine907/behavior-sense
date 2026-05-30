"""
Agent数据库模型
"""
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


def _utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class AgentProfileDB(Base):
    """Agent画像表"""
    __tablename__ = "agent_profiles"

    agent_id = Column(String(128), primary_key=True)
    agent_name = Column(String(256), nullable=True)
    agent_type = Column(String(64), nullable=True)
    model_name = Column(String(128), nullable=True)
    framework = Column(String(64), nullable=True)
    owner = Column(String(128), nullable=True)
    organization = Column(String(128), nullable=True)
    purpose = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    status = Column(String(32), default="active")
    safety_rating = Column(String(32), default="standard")
    cost_tier = Column(String(32), default="standard")

    capabilities = Column(JSONB, default=list)
    supported_tools = Column(JSONB, default=list)
    max_context_window = Column(BigInteger, nullable=True)

    behavior_tags = Column(JSONB, default=list)
    performance_tags = Column(JSONB, default=list)
    safety_tags = Column(JSONB, default=list)
    custom_tags = Column(JSONB, default=dict)

    risk_score = Column(Float, default=0.0)
    risk_factors = Column(JSONB, default=list)

    create_time = Column(DateTime(timezone=True), default=_utc_now)
    update_time = Column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)
    first_seen = Column(DateTime(timezone=True), default=_utc_now)
    last_active = Column(DateTime(timezone=True), default=_utc_now)

    __table_args__ = (
        Index("ix_agent_profiles_status", "status"),
        Index("ix_agent_profiles_agent_type", "agent_type"),
        Index("ix_agent_profiles_owner", "owner"),
    )


class AgentStatDB(Base):
    """Agent统计表"""
    __tablename__ = "agent_stats"

    agent_id = Column(String(128), primary_key=True)

    total_events = Column(BigInteger, default=0)
    total_sessions = Column(BigInteger, default=0)
    total_tasks = Column(BigInteger, default=0)
    total_tool_calls = Column(BigInteger, default=0)
    total_llm_calls = Column(BigInteger, default=0)
    total_delegations = Column(BigInteger, default=0)

    total_prompt_tokens = Column(BigInteger, default=0)
    total_completion_tokens = Column(BigInteger, default=0)
    total_tokens = Column(BigInteger, default=0)
    total_cached_tokens = Column(BigInteger, default=0)

    total_cost_usd = Column(Float, default=0.0)

    events_1h = Column(BigInteger, default=0)
    events_1d = Column(BigInteger, default=0)
    events_7d = Column(BigInteger, default=0)
    events_30d = Column(BigInteger, default=0)

    tokens_1h = Column(BigInteger, default=0)
    tokens_1d = Column(BigInteger, default=0)
    tokens_7d = Column(BigInteger, default=0)
    tokens_30d = Column(BigInteger, default=0)

    cost_1h = Column(Float, default=0.0)
    cost_1d = Column(Float, default=0.0)
    cost_7d = Column(Float, default=0.0)
    cost_30d = Column(Float, default=0.0)

    avg_latency_ms = Column(Float, default=0.0)
    p95_latency_ms = Column(Float, default=0.0)
    success_rate = Column(Float, default=1.0)
    error_rate = Column(Float, default=0.0)
    timeout_rate = Column(Float, default=0.0)

    last_event_time = Column(DateTime(timezone=True), nullable=True)
    last_tool_call_time = Column(DateTime(timezone=True), nullable=True)
    last_llm_call_time = Column(DateTime(timezone=True), nullable=True)
    last_error_time = Column(DateTime(timezone=True), nullable=True)
    last_task_completion_time = Column(DateTime(timezone=True), nullable=True)

    update_time = Column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


class AgentTagDB(Base):
    """Agent标签表"""
    __tablename__ = "agent_tags"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    agent_id = Column(String(128), nullable=False, index=True)
    tag_name = Column(String(128), nullable=False)
    tag_value = Column(Text, nullable=False)
    source = Column(String(32), default="AUTO")
    confidence = Column(Float, default=1.0)
    expire_at = Column(DateTime(timezone=True), nullable=True)

    create_time = Column(DateTime(timezone=True), default=_utc_now)
    update_time = Column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)

    __table_args__ = (
        Index("ix_agent_tags_agent_id_tag_name", "agent_id", "tag_name", unique=True),
        Index("ix_agent_tags_tag_name", "tag_name"),
    )
