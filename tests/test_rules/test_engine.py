"""
behavior_rules 模块单元测试
"""
import pytest
from datetime import datetime

from behavior_rules.models import (
    ActionType,
    RuleCondition,
    RuleAction,
    Rule,
    RuleMatchResult,
)
from behavior_rules.engine import (
    RuleEngine,
    RuleEngineError,
    ConditionEvalError,
    get_rule_engine,
)


class TestRuleModels:
    """规则模型测试"""

    def test_create_rule(self):
        """测试创建规则"""
        rule = Rule(
            id="rule_001",
            name="高价值用户",
            condition="purchase_count >= 5",
            priority=1,
        )
        assert rule.id == "rule_001"
        assert rule.name == "高价值用户"
        assert rule.enabled is True
        assert rule.version == 1

    def test_create_rule_with_actions(self):
        """测试创建带动作的规则"""
        rule = Rule(
            id="rule_001",
            name="高价值用户",
            condition="purchase_count >= 5",
            actions=[
                RuleAction(type=ActionType.TAG_USER, params={"tags": ["vip"]})
            ],
        )
        assert len(rule.actions) == 1
        assert rule.actions[0].type == ActionType.TAG_USER

    def test_rule_condition_to_expression(self):
        """测试条件转换表达式"""
        cond = RuleCondition(field="purchase_count", operator=">=", value=5)
        expr = cond.to_expression()
        assert expr == "purchase_count >= 5"

    def test_rule_condition_in_operator(self):
        """测试 in 操作符"""
        cond = RuleCondition(field="level", operator="in", value=["vip", "svip"])
        expr = cond.to_expression()
        assert "in" in expr

    def test_rule_action_default_values(self):
        """测试动作默认值"""
        action = RuleAction(type=ActionType.TAG_USER)
        assert action.params == {}
        assert action.async_exec is True
        assert action.retry_count == 3
        assert action.retry_delay == 1.0


class TestRuleEngine:
    """规则引擎测试"""

    @pytest.fixture
    def engine(self):
        """创建规则引擎实例"""
        return RuleEngine()

    @pytest.fixture
    def sample_rule(self):
        """创建示例规则"""
        return Rule(
            id="test_rule",
            name="测试规则",
            condition="purchase_count >= 5 and total_amount > 1000",
            priority=1,
            enabled=True,
            actions=[
                RuleAction(type=ActionType.TAG_USER, params={"tags": ["high_value"]})
            ],
        )

    def test_create_engine(self, engine):
        """测试创建引擎"""
        assert engine is not None
        assert len(engine.get_all_rules()) == 0

    def test_register_rule(self, engine, sample_rule):
        """测试注册规则"""
        engine.register_rule(sample_rule)
        assert len(engine.get_all_rules()) == 1
        assert engine.get_rule("test_rule") == sample_rule

    def test_unregister_rule(self, engine, sample_rule):
        """测试注销规则"""
        engine.register_rule(sample_rule)
        result = engine.unregister_rule("test_rule")
        assert result is True
        assert len(engine.get_all_rules()) == 0

    def test_unregister_nonexistent_rule(self, engine):
        """测试注销不存在的规则"""
        result = engine.unregister_rule("nonexistent")
        assert result is False

    def test_evaluate_simple_condition(self, engine):
        """测试简单条件评估"""
        engine.register_rule(Rule(
            id="simple",
            name="简单规则",
            condition="purchase_count >= 5",
            priority=1,
        ))

        context = {"purchase_count": 10}
        matched = engine.evaluate(context)
        assert len(matched) == 1

    def test_evaluate_complex_condition(self, engine, sample_rule):
        """测试复杂条件评估"""
        engine.register_rule(sample_rule)

        # 匹配的情况
        context = {"purchase_count": 10, "total_amount": 5000}
        matched = engine.evaluate(context)
        assert len(matched) == 1

        # 不匹配的情况
        context = {"purchase_count": 10, "total_amount": 500}
        matched = engine.evaluate(context)
        assert len(matched) == 0

    def test_evaluate_with_disabled_rule(self, engine):
        """测试禁用的规则不评估"""
        engine.register_rule(Rule(
            id="disabled",
            name="禁用规则",
            condition="1 == 1",  # 总是 True
            priority=1,
            enabled=False,
        ))

        matched = engine.evaluate({})
        assert len(matched) == 0

    def test_evaluate_priority_order(self, engine):
        """测试优先级排序"""
        engine.register_rule(Rule(id="low", name="低优先级", condition="1 == 1", priority=1))
        engine.register_rule(Rule(id="high", name="高优先级", condition="1 == 1", priority=10))
        engine.register_rule(Rule(id="medium", name="中优先级", condition="1 == 1", priority=5))

        matched = engine.evaluate({})
        assert len(matched) == 3
        # 高优先级在前
        assert matched[0].id == "high"
        assert matched[1].id == "medium"
        assert matched[2].id == "low"

    def test_evaluate_specific_rules(self, engine):
        """测试评估指定规则"""
        engine.register_rule(Rule(id="rule1", name="规则1", condition="1 == 1", priority=1))
        engine.register_rule(Rule(id="rule2", name="规则2", condition="1 == 2", priority=1))

        matched = engine.evaluate({}, rule_ids=["rule1"])
        assert len(matched) == 1
        assert matched[0].id == "rule1"

    def test_evaluate_with_undefined_variable(self, engine):
        """测试未定义变量"""
        engine.register_rule(Rule(
            id="test",
            name="测试",
            condition="undefined_var > 5",
            priority=1,
        ))

        # 未定义变量应该被跳过，不抛异常
        matched = engine.evaluate({})
        assert len(matched) == 0

    def test_multiple_rules_matching(self, engine):
        """测试多规则同时匹配"""
        engine.register_rule(Rule(
            id="rule1",
            name="规则1",
            condition="value > 5",
            priority=1,
        ))
        engine.register_rule(Rule(
            id="rule2",
            name="规则2",
            condition="value < 20",
            priority=2,
        ))
        engine.register_rule(Rule(
            id="rule3",
            name="规则3",
            condition="value == 10",
            priority=3,
        ))

        matched = engine.evaluate({"value": 10})
        assert len(matched) == 3

    def test_rule_override(self, engine):
        """测试同ID规则覆盖"""
        engine.register_rule(Rule(
            id="rule1",
            name="原规则",
            condition="value > 100",
            priority=1,
        ))
        engine.register_rule(Rule(
            id="rule1",
            name="新规则",
            condition="value > 5",  # 更宽松的条件
            priority=1,
        ))

        # 应该只有一个规则（后者覆盖前者）
        assert len(engine.get_all_rules()) == 1
        matched = engine.evaluate({"value": 10})
        assert len(matched) == 1

    def test_evaluate_with_syntax_error(self, engine):
        """测试条件语法错误"""
        engine.register_rule(Rule(
            id="syntax_error",
            name="语法错误规则",
            condition="value >>> 5",  # 无效语法
            priority=1,
        ))

        # 语法错误应该被跳过
        matched = engine.evaluate({"value": 10})
        assert len(matched) == 0

    def test_evaluate_empty_condition(self, engine):
        """测试空条件"""
        engine.register_rule(Rule(
            id="empty",
            name="空条件",
            condition="",
            priority=1,
        ))

        # 空条件应该被跳过或抛错
        matched = engine.evaluate({})
        assert len(matched) == 0


class TestSafeEval:
    """安全表达式评估测试"""

    @pytest.fixture
    def engine(self):
        return RuleEngine()

    def test_eval_comparison(self, engine):
        """测试比较操作"""
        assert engine._safe_eval("a > 5", {"a": 10}) is True
        assert engine._safe_eval("a > 5", {"a": 3}) is False
        assert engine._safe_eval("a >= 5", {"a": 5}) is True
        assert engine._safe_eval("a < 5", {"a": 3}) is True
        assert engine._safe_eval("a <= 5", {"a": 5}) is True
        assert engine._safe_eval("a == 5", {"a": 5}) is True
        assert engine._safe_eval("a != 5", {"a": 3}) is True

    def test_eval_boolean(self, engine):
        """测试布尔操作"""
        assert engine._safe_eval("a and b", {"a": True, "b": True}) is True
        assert engine._safe_eval("a and b", {"a": True, "b": False}) is False
        assert engine._safe_eval("a or b", {"a": False, "b": True}) is True
        assert engine._safe_eval("not a", {"a": False}) is True

    def test_eval_arithmetic(self, engine):
        """测试算术操作在条件中的使用"""
        # _safe_eval 返回布尔值，测试算术表达式在比较中
        assert engine._safe_eval("a + b > 2", {"a": 1, "b": 2}) is True
        assert engine._safe_eval("a - b == 3", {"a": 5, "b": 2}) is True
        assert engine._safe_eval("a * b >= 12", {"a": 3, "b": 4}) is True
        assert engine._safe_eval("a / b == 5", {"a": 10, "b": 2}) is True

    def test_eval_in_operator(self, engine):
        """测试 in 操作"""
        assert engine._safe_eval("a in b", {"a": 1, "b": [1, 2, 3]}) is True
        assert engine._safe_eval("a not in b", {"a": 5, "b": [1, 2, 3]}) is True

    def test_eval_function_calls(self, engine):
        """测试允许的函数调用在条件中"""
        assert engine._safe_eval("len(a) == 3", {"a": [1, 2, 3]}) is True
        assert engine._safe_eval("max(a, b) == 2", {"a": 1, "b": 2}) is True
        assert engine._safe_eval("min(a, b) == 1", {"a": 1, "b": 2}) is True
        assert engine._safe_eval("sum(a) == 6", {"a": [1, 2, 3]}) is True

    def test_eval_forbidden_code(self, engine):
        """测试禁止的代码执行"""
        # 应该拒绝危险的函数调用
        with pytest.raises(ConditionEvalError):
            engine._safe_eval("__import__('os').system('ls')", {})

        with pytest.raises(ConditionEvalError):
            engine._safe_eval("open('/etc/passwd')", {})

    def test_eval_complex_expression(self, engine):
        """测试复杂表达式"""
        context = {"purchase_count": 10, "total_amount": 5000, "level": "vip"}
        result = engine._safe_eval(
            "purchase_count >= 5 and total_amount > 1000 and level in ['vip', 'svip']",
            context
        )
        assert result is True


class TestActionExecution:
    """动作执行测试"""

    @pytest.fixture
    def engine(self):
        engine = RuleEngine()

        # 注册模拟的动作处理器
        async def mock_tag_handler(params, context):
            return {"tagged": True, "tags": params.get("tags", [])}

        engine.register_action_handler(ActionType.TAG_USER, mock_tag_handler)
        return engine

    @pytest.mark.asyncio
    async def test_execute_actions(self, engine):
        """测试执行动作"""
        rule = Rule(
            id="test",
            name="测试",
            condition="1 == 1",  # 总是 True
            priority=1,
            actions=[
                RuleAction(type=ActionType.TAG_USER, params={"tags": ["vip"]})
            ],
        )
        engine.register_rule(rule)

        matched = engine.evaluate({})
        results = await engine.execute_actions(matched, {})

        assert len(results) == 1
        assert results[0].matched is True
        assert len(results[0].actions_executed) == 1

    @pytest.mark.asyncio
    async def test_evaluate_and_execute(self, engine):
        """测试评估并执行"""
        rule = Rule(
            id="test",
            name="测试",
            condition="value > 10",
            priority=1,
            actions=[
                RuleAction(type=ActionType.TAG_USER, params={"tags": ["high"]})
            ],
        )
        engine.register_rule(rule)

        results = await engine.evaluate_and_execute({"value": 20})
        assert len(results) == 1
        assert results[0].actions_executed[0]["success"] is True

    @pytest.mark.asyncio
    async def test_execute_without_handler(self):
        """测试没有处理器的情况"""
        engine = RuleEngine()  # 没有注册处理器

        rule = Rule(
            id="test",
            name="测试",
            condition="1 == 1",  # 总是 True
            priority=1,
            actions=[
                RuleAction(type=ActionType.TAG_USER, params={"tags": ["vip"]})
            ],
        )
        engine.register_rule(rule)

        matched = engine.evaluate({})
        results = await engine.execute_actions(matched, {})

        # 应该记录错误但不抛异常
        assert results[0].actions_executed[0]["success"] is False
        assert "No handler registered" in results[0].actions_executed[0]["error"]

    @pytest.mark.asyncio
    async def test_action_retry_on_failure(self):
        """测试动作执行失败重试"""
        engine = RuleEngine()
        call_count = 0

        async def failing_handler(params, context):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return {"success": True}

        engine.register_action_handler(ActionType.TAG_USER, failing_handler)

        rule = Rule(
            id="test",
            name="测试",
            condition="1 == 1",
            priority=1,
            actions=[
                RuleAction(
                    type=ActionType.TAG_USER,
                    params={"tags": ["vip"]},
                    retry_count=3,
                    retry_delay=0.1,
                )
            ],
        )
        engine.register_rule(rule)

        matched = engine.evaluate({})
        results = await engine.execute_actions(matched, {})

        # 应该重试成功
        assert call_count == 3
        assert results[0].actions_executed[0]["success"] is True

    @pytest.mark.asyncio
    async def test_action_retry_exhausted(self):
        """测试动作重试次数耗尽"""
        engine = RuleEngine()
        call_count = 0

        async def always_failing_handler(params, context):
            nonlocal call_count
            call_count += 1
            raise Exception("Always fails")

        engine.register_action_handler(ActionType.TAG_USER, always_failing_handler)

        rule = Rule(
            id="test",
            name="测试",
            condition="1 == 1",
            priority=1,
            actions=[
                RuleAction(
                    type=ActionType.TAG_USER,
                    params={"tags": ["vip"]},
                    retry_count=2,
                    retry_delay=0.1,
                )
            ],
        )
        engine.register_rule(rule)

        matched = engine.evaluate({})
        results = await engine.execute_actions(matched, {})

        # 应该重试 2 次后失败
        assert call_count == 2
        assert results[0].actions_executed[0]["success"] is False
        assert "Always fails" in results[0].actions_executed[0]["error"]

    @pytest.mark.asyncio
    async def test_multiple_actions(self):
        """测试多动作执行"""
        engine = RuleEngine()

        async def tag_handler(params, context):
            return {"tags": params.get("tags", [])}

        async def alert_handler(params, context):
            return {"alerted": True}

        engine.register_action_handler(ActionType.TAG_USER, tag_handler)
        engine.register_action_handler(ActionType.ALERT, alert_handler)

        rule = Rule(
            id="test",
            name="测试",
            condition="1 == 1",
            priority=1,
            actions=[
                RuleAction(type=ActionType.TAG_USER, params={"tags": ["vip"]}),
                RuleAction(type=ActionType.ALERT, params={"message": "测试告警"}),
            ],
        )
        engine.register_rule(rule)

        matched = engine.evaluate({})
        results = await engine.execute_actions(matched, {})

        assert len(results[0].actions_executed) == 2
        assert results[0].actions_executed[0]["success"] is True
        assert results[0].actions_executed[1]["success"] is True


class TestGlobalEngine:
    """全局引擎测试"""

    def test_get_global_engine(self):
        """测试获取全局引擎"""
        engine1 = get_rule_engine()
        engine2 = get_rule_engine()
        assert engine1 is engine2

    def test_global_engine_is_thread_safe(self):
        """测试全局引擎线程安全"""
        import threading

        engines = []

        def get_engine():
            engines.append(get_rule_engine())

        threads = [threading.Thread(target=get_engine) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 所有线程应该获取到同一个实例
        assert all(e is engines[0] for e in engines)
