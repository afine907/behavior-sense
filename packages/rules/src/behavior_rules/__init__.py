"""
Behavior Rules 模块

规则引擎服务，提供规则定义、匹配和动作触发功能。
"""
from behavior_rules.engine import ConditionEvalError, RuleEngine, RuleEngineError, get_rule_engine
from behavior_rules.loader import BaseRuleLoader, DbRuleLoader, RuleLoaderError, YamlRuleLoader
from behavior_rules.models import (
    ActionType,
    EvaluateRequest,
    EvaluateResponse,
    Rule,
    RuleAction,
    RuleCondition,
    RuleCreate,
    RuleMatchResult,
    RuleUpdate,
)

__all__ = [
    # 模型
    "ActionType",
    "RuleCondition",
    "RuleAction",
    "Rule",
    "RuleCreate",
    "RuleUpdate",
    "RuleMatchResult",
    "EvaluateRequest",
    "EvaluateResponse",
    # 引擎
    "RuleEngine",
    "RuleEngineError",
    "ConditionEvalError",
    "get_rule_engine",
    # 加载器
    "BaseRuleLoader",
    "YamlRuleLoader",
    "DbRuleLoader",
    "RuleLoaderError",
]
