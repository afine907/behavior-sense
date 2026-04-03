"""
BehaviorSense 核心库
"""
from behavior_core.models import (
    EventType,
    UserBehavior,
    StandardEvent,
    AggregationResult,
    AlertEvent,
    UserStatus,
    UserLevel,
    TagSource,
    TagValue,
    UserTags,
    UserProfile,
    UserStat,
)
from behavior_core.config.settings import Settings, get_settings, settings

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
]
