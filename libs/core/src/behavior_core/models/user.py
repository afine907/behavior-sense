"""
用户相关模型
"""
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserLevel(str, Enum):
    """用户等级"""
    NEW = "new"
    NORMAL = "normal"
    VIP = "vip"
    SVIP = "svip"


class TagSource(str, Enum):
    """标签来源"""
    AUTO = "AUTO"          # 自动打标
    MANUAL = "MANUAL"      # 人工打标
    AUDIT = "AUDIT"        # 审核打标
    RULE = "RULE"          # 规则触发
    IMPORT = "IMPORT"      # 导入


def _utc_now() -> datetime:
    """获取当前 UTC 时间"""
    return datetime.now(UTC)


class TagValue(BaseModel):
    """标签值模型"""
    value: str
    timestamp: datetime = Field(default_factory=_utc_now)
    confidence: float = 1.0
    source: TagSource = TagSource.AUTO
    expire_at: datetime | None = None


class UserTags(BaseModel):
    """用户标签模型"""
    user_id: str
    tags: dict[str, "TagValue"] = Field(default_factory=dict)
    last_update: datetime = Field(default_factory=_utc_now)

    def get_tag(self, tag_name: str) -> "TagValue | None":
        """获取标签值"""
        return self.tags.get(tag_name)

    def set_tag(
        self,
        tag_name: str,
        value: str,
        source: TagSource = TagSource.AUTO,
        confidence: float = 1.0,
    ) -> None:
        """设置标签"""
        self.tags[tag_name] = TagValue(
            value=value,
            source=source,
            confidence=confidence,
        )
        self.last_update = _utc_now()

    def remove_tag(self, tag_name: str) -> bool:
        """移除标签"""
        if tag_name in self.tags:
            del self.tags[tag_name]
            self.last_update = _utc_now()
            return True
        return False


class UserProfile(BaseModel):
    """用户画像模型"""
    user_id: str
    basic_info: dict[str, Any] = Field(default_factory=dict)
    behavior_tags: list[str] = Field(default_factory=list)
    stat_tags: dict[str, Any] = Field(default_factory=dict)
    predict_tags: dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "low"
    create_time: datetime = Field(default_factory=_utc_now)
    update_time: datetime = Field(default_factory=_utc_now)


class UserStat(BaseModel):
    """用户统计模型"""
    user_id: str
    # 基础统计
    total_events: int = 0
    total_sessions: int = 0
    total_purchases: int = 0
    total_amount: float = 0.0

    # 时间窗口统计
    events_1d: int = 0
    events_7d: int = 0
    events_30d: int = 0

    purchases_1d: int = 0
    purchases_7d: int = 0
    purchases_30d: int = 0

    amount_1d: float = 0.0
    amount_7d: float = 0.0
    amount_30d: float = 0.0

    # 最近活动
    last_event_time: datetime | None = None
    last_purchase_time: datetime | None = None
    last_login_time: datetime | None = None

    update_time: datetime = Field(default_factory=_utc_now)
