"""
用户行为事件模型
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    """事件类型枚举"""
    VIEW = "view"
    CLICK = "click"
    SEARCH = "search"
    PURCHASE = "purchase"
    COMMENT = "comment"
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    FAVORITE = "favorite"
    SHARE = "share"


def _utc_now() -> datetime:
    """获取当前 UTC 时间"""
    return datetime.now(timezone.utc)


class UserBehavior(BaseModel):
    """用户行为事件模型"""
    model_config = ConfigDict(
        use_enum_values=True,
    )

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    event_type: EventType
    timestamp: datetime = Field(default_factory=_utc_now)
    session_id: str | None = None
    page_url: str | None = None
    referrer: str | None = None
    user_agent: str | None = None
    ip_address: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class StandardEvent(BaseModel):
    """标准化事件模型"""
    event_id: str
    user_id: str
    event_type: str
    timestamp: datetime
    processed_at: datetime = Field(default_factory=_utc_now)
    session_id: str | None = None
    page_url: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class AggregationResult(BaseModel):
    """聚合结果模型"""
    user_id: str
    window_start: datetime
    window_end: datetime
    event_count: int = 0
    view_count: int = 0
    click_count: int = 0
    purchase_count: int = 0
    total_amount: float = 0.0
    unique_sessions: int = 0
    processed_at: datetime = Field(default_factory=_utc_now)


class AlertEvent(BaseModel):
    """告警事件模型"""
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: str
    user_id: str
    severity: str = "medium"  # low, medium, high, critical
    message: str
    trigger_data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=_utc_now)
    resolved: bool = False
