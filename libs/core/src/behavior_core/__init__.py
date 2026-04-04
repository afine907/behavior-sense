"""
BehaviorSense 核心库
"""
from behavior_core.config.settings import Settings, get_settings, settings
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
