"""
规则动作处理器

提供规则引擎的动作处理器实现。
"""
from behavior_rules.actions.audit import (
    batch_trigger_audit,
    get_audit_order,
    get_pending_audits,
    submit_review,
    trigger_audit,
)
from behavior_rules.actions.tagging import batch_tag_users, get_user_tags, tag_user

__all__ = [
    # 标签动作
    "tag_user",
    "get_user_tags",
    "batch_tag_users",
    # 审核动作
    "trigger_audit",
    "get_audit_order",
    "get_pending_audits",
    "submit_review",
    "batch_trigger_audit",
]
