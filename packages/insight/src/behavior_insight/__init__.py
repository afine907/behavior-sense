"""
BehaviorSense Insight 服务
洞察分析服务 - 标签管理、用户画像、分析报表
"""
from behavior_insight.main import app
from behavior_insight.repositories.user_repo import UserRepository
from behavior_insight.services.tag_service import TagService

__all__ = [
    "TagService",
    "UserRepository",
    "app",
]
