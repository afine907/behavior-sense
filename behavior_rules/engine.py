"""
规则引擎实现

实现规则注册、评估和动作执行的核心逻辑。
"""
import asyncio
import time
import logging
from typing import Any, Callable, Coroutine
from collections.abc import Awaitable

from behavior_rules.models import Rule, RuleAction, RuleMatchResult


logger = logging.getLogger(__name__)

# 动作处理器类型
ActionHandler = Callable[[dict[str, Any], dict[str, Any]], Awaitable[Any]]


class RuleEngineError(Exception):
    """规则引擎异常"""
    pass


class ConditionEvalError(RuleEngineError):
    """条件评估异常"""
    pass


class RuleEngine:
    """
    规则引擎

    负责规则的管理、评估和动作执行。

    特性：
    - 支持规则优先级排序
    - 安全的条件表达式求值
    - 异步动作执行
    - 动作处理器注册机制
    """

    def __init__(self):
        self._rules: dict[str, Rule] = {}
        self._action_handlers: dict[str, ActionHandler] = {}
        self._lock = asyncio.Lock()

    def register_rule(self, rule: Rule) -> None:
        """
        注册规则

        Args:
            rule: 规则对象
        """
        self._rules[rule.id] = rule
        logger.info(f"Registered rule: {rule.id} - {rule.name}")

    def unregister_rule(self, rule_id: str) -> bool:
        """
        注销规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功注销
        """
        if rule_id in self._rules:
            del self._rules[rule_id]
            logger.info(f"Unregistered rule: {rule_id}")
            return True
        return False

    def get_rule(self, rule_id: str) -> Rule | None:
        """
        获取规则

        Args:
            rule_id: 规则ID

        Returns:
            规则对象或None
        """
        return self._rules.get(rule_id)

    def get_all_rules(self) -> list[Rule]:
        """
        获取所有规则

        Returns:
            规则列表
        """
        return list(self._rules.values())

    def register_action_handler(
        self,
        action_type: str,
        handler: ActionHandler
    ) -> None:
        """
        注册动作处理器

        Args:
            action_type: 动作类型
            handler: 处理函数，接收 (params, context) 参数
        """
        self._action_handlers[action_type] = handler
        logger.info(f"Registered action handler: {action_type}")

    def unregister_action_handler(self, action_type: str) -> bool:
        """
        注销动作处理器

        Args:
            action_type: 动作类型

        Returns:
            是否成功注销
        """
        if action_type in self._action_handlers:
            del self._action_handlers[action_type]
            logger.info(f"Unregistered action handler: {action_type}")
            return True
        return False

    def evaluate(
        self,
        context: dict[str, Any],
        rule_ids: list[str] | None = None
    ) -> list[Rule]:
        """
        评估规则，返回命中的规则

        Args:
            context: 评估上下文，包含条件表达式所需的变量
            rule_ids: 指定评估的规则ID列表，为None则评估所有规则

        Returns:
            命中的规则列表，按优先级降序排列
        """
        matched: list[Rule] = []

        # 获取待评估的规则
        if rule_ids:
            rules_to_evaluate = [
                self._rules[rid] for rid in rule_ids
                if rid in self._rules
            ]
        else:
            rules_to_evaluate = list(self._rules.values())

        # 按优先级降序排序
        sorted_rules = sorted(
            rules_to_evaluate,
            key=lambda r: r.priority,
            reverse=True
        )

        for rule in sorted_rules:
            if not rule.enabled:
                continue

            try:
                if self._safe_eval(rule.condition, context):
                    matched.append(rule)
                    logger.debug(f"Rule matched: {rule.id} - {rule.name}")
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {e}")

        return matched

    def _safe_eval(self, condition: str, context: dict[str, Any]) -> bool:
        """
        安全地评估条件表达式

        使用受限的执行环境，防止恶意代码执行。

        Args:
            condition: Python 条件表达式
            context: 评估上下文

        Returns:
            条件是否为真

        Raises:
            ConditionEvalError: 条件评估失败
        """
        try:
            # 限制可用的内置函数和名称
            allowed_builtins = {
                "True": True,
                "False": False,
                "None": None,
                "abs": abs,
                "len": len,
                "max": max,
                "min": min,
                "sum": sum,
                "any": any,
                "all": all,
                "isinstance": isinstance,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
            }

            # 创建安全的执行环境
            safe_globals = {"__builtins__": allowed_builtins}
            safe_locals = {**context}

            result = eval(condition, safe_globals, safe_locals)
            return bool(result)

        except NameError as e:
            logger.warning(f"NameError in condition evaluation: {e}")
            raise ConditionEvalError(f"Undefined variable: {e}")
        except SyntaxError as e:
            logger.error(f"SyntaxError in condition: {e}")
            raise ConditionEvalError(f"Invalid syntax: {e}")
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            raise ConditionEvalError(f"Evaluation error: {e}")

    async def execute_actions(
        self,
        rules: list[Rule],
        context: dict[str, Any]
    ) -> list[RuleMatchResult]:
        """
        执行规则动作

        Args:
            rules: 要执行动作的规则列表
            context: 执行上下文

        Returns:
            执行结果列表
        """
        results: list[RuleMatchResult] = []

        for rule in rules:
            start_time = time.perf_counter()
            actions_executed: list[dict[str, Any]] = []
            error: str | None = None

            for action in rule.actions:
                handler = self._action_handlers.get(action.type.value)

                if handler is None:
                    logger.warning(
                        f"No handler registered for action type: {action.type}"
                    )
                    actions_executed.append({
                        "action": action.type.value,
                        "error": f"No handler registered for action type: {action.type}"
                    })
                    continue

                try:
                    # 执行动作处理器（无论 async_exec 与否都是异步）
                    result = await self._execute_with_retry(
                        handler, action, context
                    )

                    actions_executed.append({
                        "action": action.type.value,
                        "result": result,
                        "success": True
                    })
                    logger.debug(
                        f"Action executed: {action.type.value} for rule {rule.id}"
                    )

                except Exception as e:
                    error_msg = f"Action execution failed: {e}"
                    logger.error(f"{error_msg} for rule {rule.id}")
                    actions_executed.append({
                        "action": action.type.value,
                        "error": str(e),
                        "success": False
                    })
                    error = error_msg

            execution_time = (time.perf_counter() - start_time) * 1000

            results.append(RuleMatchResult(
                rule_id=rule.id,
                rule_name=rule.name,
                matched=True,
                context=context,
                actions_executed=actions_executed,
                execution_time_ms=round(execution_time, 2),
                error=error
            ))

        return results

    async def _execute_with_retry(
        self,
        handler: ActionHandler,
        action: RuleAction,
        context: dict[str, Any]
    ) -> Any:
        """
        带重试的动作执行

        Args:
            handler: 动作处理器
            action: 动作对象
            context: 执行上下文

        Returns:
            处理器返回结果

        Raises:
            Exception: 重试次数用尽后抛出最后一次异常
        """
        last_exception: Exception | None = None

        for attempt in range(action.retry_count):
            try:
                return await handler(action.params, context)
            except Exception as e:
                last_exception = e
                if attempt < action.retry_count - 1:
                    logger.warning(
                        f"Action execution attempt {attempt + 1} failed, "
                        f"retrying in {action.retry_delay}s: {e}"
                    )
                    await asyncio.sleep(action.retry_delay)

        raise last_exception

    async def evaluate_and_execute(
        self,
        context: dict[str, Any],
        rule_ids: list[str] | None = None,
        execute_actions: bool = True
    ) -> list[RuleMatchResult]:
        """
        评估规则并执行动作

        这是一个便捷方法，组合了 evaluate 和 execute_actions。

        Args:
            context: 评估上下文
            rule_ids: 指定评估的规则ID列表
            execute_actions: 是否执行动作

        Returns:
            匹配结果列表
        """
        matched_rules = self.evaluate(context, rule_ids)

        if execute_actions and matched_rules:
            return await self.execute_actions(matched_rules, context)

        # 不执行动作时返回空动作列表
        return [
            RuleMatchResult(
                rule_id=rule.id,
                rule_name=rule.name,
                matched=True,
                context=context,
                actions_executed=[],
                execution_time_ms=0.0
            )
            for rule in matched_rules
        ]


# 全局规则引擎实例
_engine: RuleEngine | None = None


def get_rule_engine() -> RuleEngine:
    """获取全局规则引擎实例"""
    global _engine
    if _engine is None:
        _engine = RuleEngine()
    return _engine
