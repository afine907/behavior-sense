"""
规则引擎实现

实现规则注册、评估和动作执行的核心逻辑。
"""
import ast
import asyncio
import logging
import operator
import threading
import time
from collections.abc import Awaitable, Callable
from typing import Any

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

        使用 AST 解析替代 eval()，只允许有限的表达式类型，
        防止恶意代码执行。

        Args:
            condition: Python 条件表达式
            context: 评估上下文

        Returns:
            条件是否为真

        Raises:
            ConditionEvalError: 条件评估失败
        """
        try:
            # 解析条件表达式为 AST
            tree = ast.parse(condition, mode='eval')
            result = self._eval_ast_node(tree.body, context)
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

    def _eval_ast_node(self, node: ast.AST, context: dict[str, Any]) -> Any:
        """
        递归评估 AST 节点

        只允许安全的节点类型，拒绝危险的调用。

        Args:
            node: AST 节点
            context: 评估上下文

        Returns:
            评估结果

        Raises:
            ConditionEvalError: 遇到不允许的节点类型
        """
        # 允许的字面量 (Python 3.8+ 使用 ast.Constant)
        if isinstance(node, ast.Constant):
            return node.value

        # Python 3.7 兼容 (已在 Python 3.12 中移除)
        try:
            if isinstance(node, ast.Num):
                return node.n
            if isinstance(node, ast.Str):
                return node.s
            if isinstance(node, (ast.True_, ast.False_)):
                return isinstance(node, ast.True_)
            if isinstance(node, ast.None_):
                return None
        except AttributeError:
            # Python 3.12+ 中这些类型已移除，使用 ast.Constant 替代
            pass

        # 允许变量名
        if isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            # 允许的内置常量
            if node.id in ("True", "False", "None"):
                return {"True": True, "False": False, "None": None}[node.id]
            raise NameError(f"Undefined variable: {node.id}")

        # 允许二元操作
        if isinstance(node, ast.BinOp):
            left = self._eval_ast_node(node.left, context)
            right = self._eval_ast_node(node.right, context)
            ops = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.FloorDiv: operator.floordiv,
                ast.Mod: operator.mod,
                ast.Pow: operator.pow,
            }
            op_type = type(node.op)
            if op_type in ops:
                return ops[op_type](left, right)
            raise ConditionEvalError(f"Unsupported binary operator: {op_type}")

        # 允许一元操作
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_ast_node(node.operand, context)
            if isinstance(node.op, ast.Not):
                return not operand
            if isinstance(node.op, ast.USub):
                return -operand
            if isinstance(node.op, ast.UAdd):
                return +operand
            raise ConditionEvalError(f"Unsupported unary operator: {type(node.op)}")

        # 允许比较操作
        if isinstance(node, ast.Compare):
            left = self._eval_ast_node(node.left, context)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_ast_node(comparator, context)
                ops = {
                    ast.Eq: operator.eq,
                    ast.NotEq: operator.ne,
                    ast.Lt: operator.lt,
                    ast.LtE: operator.le,
                    ast.Gt: operator.gt,
                    ast.GtE: operator.ge,
                    ast.In: lambda a, b: a in b,
                    ast.NotIn: lambda a, b: a not in b,
                }
                op_type = type(op)
                if op_type in ops:
                    if not ops[op_type](left, right):
                        return False
                else:
                    raise ConditionEvalError(f"Unsupported comparison operator: {op_type}")
                left = right
            return True

        # 允许布尔操作
        if isinstance(node, ast.BoolOp):
            values = [self._eval_ast_node(v, context) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
            raise ConditionEvalError(f"Unsupported boolean operator: {type(node.op)}")

        # 允许条件表达式 (三元运算符)
        if isinstance(node, ast.IfExp):
            test = self._eval_ast_node(node.test, context)
            if test:
                return self._eval_ast_node(node.body, context)
            return self._eval_ast_node(node.orelse, context)

        # 允许列表
        if isinstance(node, ast.List):
            return [self._eval_ast_node(el, context) for el in node.elts]

        # 允许字典
        if isinstance(node, ast.Dict):
            keys = [self._eval_ast_node(k, context) for k in node.keys]
            values = [self._eval_ast_node(v, context) for v in node.values]
            return dict(zip(keys, values))

        # 允许元组
        if isinstance(node, ast.Tuple):
            return tuple(self._eval_ast_node(el, context) for el in node.elts)

        # 允许下标访问
        if isinstance(node, ast.Subscript):
            value = self._eval_ast_node(node.value, context)
            if isinstance(node.slice, ast.AST):
                slice_val = self._eval_ast_node(node.slice, context)
            else:
                slice_val = node.slice
            return value[slice_val]

        # 允许属性访问 (受限)
        if isinstance(node, ast.Attribute):
            value = self._eval_ast_node(node.value, context)
            attr = node.attr
            # 只允许访问简单属性
            if hasattr(value, attr) and not attr.startswith('_'):
                return getattr(value, attr)
            raise ConditionEvalError(f"Access to attribute '{attr}' is not allowed")

        # 允许简单的函数调用 (len, str, int, float, bool, abs, max, min, sum, any, all)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                allowed_funcs = {
                    "len": len, "str": str, "int": int, "float": float,
                    "bool": bool, "abs": abs, "max": max, "min": min,
                    "sum": sum, "any": any, "all": all, "list": list,
                    "dict": dict, "set": set, "tuple": tuple,
                }
                if func_name in allowed_funcs:
                    args = [self._eval_ast_node(arg, context) for arg in node.args]
                    return allowed_funcs[func_name](*args)
            raise ConditionEvalError(f"Function call '{ast.dump(node.func)}' is not allowed")

        # 拒绝所有其他节点类型
        raise ConditionEvalError(f"Unsupported expression type: {type(node).__name__}")

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
                        "error": f"No handler registered for action type: {action.type}",
                        "success": False
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
_engine_lock = threading.Lock()


def get_rule_engine() -> RuleEngine:
    """获取全局规则引擎实例 (线程安全)"""
    global _engine
    if _engine is None:
        with _engine_lock:
            # 双重检查锁定
            if _engine is None:
                _engine = RuleEngine()
    return _engine
