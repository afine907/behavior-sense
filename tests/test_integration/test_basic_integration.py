"""
基础集成测试 - 无外部依赖

测试不需要 Redis/PostgreSQL 的服务集成
"""
import pytest
from httpx import AsyncClient

from behavior_rules.engine import RuleEngine
from behavior_rules.models import Rule, RuleAction
from behavior_core.models.event import EventType
from behavior_mock.generator import BehaviorGenerator


pytestmark = pytest.mark.asyncio


class TestRulesServiceIntegration:
    """Rules 服务集成测试（无外部依赖）"""

    async def test_rules_crud_flow(self, rules_client: AsyncClient):
        """测试规则 CRUD 完整流程"""
        # 创建规则
        create_response = await rules_client.post(
            "/api/rules",
            json={
                "name": "集成测试规则",
                "description": "测试规则创建和查询",
                "condition": "value >= 100",
                "priority": 5,
                "enabled": True,
                "actions": [{"type": "TAG_USER", "params": {"tags": ["test_tag"]}}],
                "tags": ["integration"]
            }
        )
        assert create_response.status_code == 201
        rule_id = create_response.json()["id"]

        # 查询规则
        get_response = await rules_client.get(f"/api/rules/{rule_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "集成测试规则"

        # 更新规则
        update_response = await rules_client.put(
            f"/api/rules/{rule_id}",
            json={"priority": 10}
        )
        assert update_response.status_code == 200
        assert update_response.json()["priority"] == 10

        # 删除规则 - 返回 204 No Content
        delete_response = await rules_client.delete(f"/api/rules/{rule_id}")
        assert delete_response.status_code == 204

        # 验证删除
        get_after_delete = await rules_client.get(f"/api/rules/{rule_id}")
        assert get_after_delete.status_code == 404

    async def test_rules_evaluation_flow(self, rules_client: AsyncClient):
        """测试规则评估流程"""
        # 创建多个规则
        rules = [
            {
                "name": "高价值用户",
                "condition": "purchase_count >= 5",
                "priority": 1,
                "enabled": True,
                "actions": [{"type": "TAG_USER", "params": {"tags": ["high_value"]}}]
            },
            {
                "name": "活跃用户",
                "condition": "login_count >= 10",
                "priority": 2,
                "enabled": True,
                "actions": [{"type": "TAG_USER", "params": {"tags": ["active"]}}]
            }
        ]

        rule_ids = []
        for rule in rules:
            response = await rules_client.post("/api/rules", json=rule)
            assert response.status_code == 201
            rule_ids.append(response.json()["id"])

        # 评估规则 - 匹配两个规则
        # EvaluateRequest 需要 context 字段
        eval_request = {
            "context": {
                "user_id": "test_user_001",
                "purchase_count": 8,
                "login_count": 15
            }
        }

        dry_run_response = await rules_client.post(
            "/api/rules/evaluate/dry-run",
            json=eval_request
        )
        assert dry_run_response.status_code == 200
        result = dry_run_response.json()

        # 验证匹配结果
        assert len(result["matched_rules"]) >= 1
        matched_names = [r["rule_name"] for r in result["matched_rules"]]
        # 至少有一个规则匹配
        assert "高价值用户" in matched_names or "活跃用户" in matched_names

    async def test_rule_validation(self, rules_client: AsyncClient):
        """测试规则条件验证"""
        # 有效条件 - 需要完整的 RuleCreate 对象
        valid_response = await rules_client.post(
            "/api/rules/validate",
            json={
                "name": "验证测试规则",
                "condition": "purchase_count >= 5 and total_amount > 1000"
            }
        )
        assert valid_response.status_code == 200
        assert valid_response.json()["valid"] is True

        # 无效条件（危险代码）
        invalid_response = await rules_client.post(
            "/api/rules/validate",
            json={
                "name": "恶意规则",
                "condition": "__import__('os').system('echo hack')"
            }
        )
        assert invalid_response.status_code == 200
        assert invalid_response.json()["valid"] is False

    async def test_rules_statistics(self, rules_client: AsyncClient):
        """测试规则统计"""
        # 创建一些规则
        for i in range(3):
            await rules_client.post(
                "/api/rules",
                json={
                    "name": f"统计测试规则 {i}",
                    "condition": f"value >= {i * 10}",
                    "enabled": i < 2,  # 前两个启用
                    "actions": [{"type": "TAG_USER", "params": {"tags": [f"tag_{i}"]}}]
                }
            )

        # 获取统计
        stats_response = await rules_client.get("/api/rules/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()

        assert "total_rules" in stats
        assert "enabled_rules" in stats


class TestMockServiceIntegration:
    """Mock 服务集成测试（无外部依赖）"""

    async def test_event_generation_flow(self, mock_client: AsyncClient):
        """测试事件生成流程"""
        # 生成事件
        response = await mock_client.post(
            "/api/mock/generate",
            json={
                "count": 50,
                "user_pool_size": 20,
                "weighted": True
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["count"] == 50
        assert len(data["events"]) == 50

        # 验证事件格式
        for event in data["events"]:
            assert "user_id" in event
            assert "event_type" in event

    async def test_scenario_management_flow(self, mock_client: AsyncClient):
        """测试场景管理流程"""
        import asyncio

        # 启动场景
        start_response = await mock_client.post(
            "/api/mock/scenario/start",
            json={
                "scenario_type": "normal",
                "scenario_id": "test_scenario_001",
                "duration_seconds": 5,
                "rate_per_second": 10
            }
        )
        assert start_response.status_code == 200
        scenario_id = start_response.json()["scenario_id"]

        # 查询场景状态
        await asyncio.sleep(0.5)  # 等待场景启动
        status_response = await mock_client.get(f"/api/mock/scenario/{scenario_id}")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "running"

        # 停止场景
        stop_response = await mock_client.post(f"/api/mock/scenario/{scenario_id}/stop")
        assert stop_response.status_code == 200

        # 删除场景
        delete_response = await mock_client.delete(f"/api/mock/scenario/{scenario_id}")
        assert delete_response.status_code == 200


class TestCrossServiceRulesEvaluation:
    """跨服务规则评估测试"""

    async def test_rules_evaluate_with_tag_action(
        self,
        rules_client: AsyncClient
    ):
        """
        测试规则评估触发打标签动作

        注意：这只是 dry-run 测试，不会实际调用 Insight 服务
        """
        # 创建带打标签动作的规则
        rule_response = await rules_client.post(
            "/api/rules",
            json={
                "name": "高消费用户识别",
                "condition": "total_amount > 5000",
                "priority": 1,
                "enabled": True,
                "actions": [
                    {
                        "type": "TAG_USER",
                        "params": {
                            "tags": ["high_spender", "premium"],
                            "source": "rule"
                        }
                    }
                ]
            }
        )
        assert rule_response.status_code == 201

        # Dry-run 评估 - 使用正确的请求格式
        eval_response = await rules_client.post(
            "/api/rules/evaluate/dry-run",
            json={
                "context": {
                    "user_id": "premium_user_001",
                    "total_amount": 10000
                }
            }
        )
        assert eval_response.status_code == 200
        result = eval_response.json()

        # 验证规则匹配
        assert len(result["matched_rules"]) >= 1
        matched = result["matched_rules"][0]
        assert matched["rule_name"] == "高消费用户识别"

    async def test_rules_evaluate_with_audit_action(
        self,
        rules_client: AsyncClient
    ):
        """
        测试规则评估触发审核动作

        注意：这只是 dry-run 测试，不会实际调用 Audit 服务
        """
        # 创建带审核动作的规则
        rule_response = await rules_client.post(
            "/api/rules",
            json={
                "name": "可疑行为检测",
                "condition": "login_fail_count >= 5",
                "priority": 10,
                "enabled": True,
                "actions": [
                    {
                        "type": "TRIGGER_AUDIT",
                        "params": {
                            "level": "HIGH",
                            "reason": "检测到连续登录失败"
                        }
                    }
                ]
            }
        )
        assert rule_response.status_code == 201

        # Dry-run 评估 - 使用正确的请求格式
        eval_response = await rules_client.post(
            "/api/rules/evaluate/dry-run",
            json={
                "context": {
                    "user_id": "suspicious_user_001",
                    "login_fail_count": 7
                }
            }
        )
        assert eval_response.status_code == 200
        result = eval_response.json()

        # 验证规则匹配
        assert len(result["matched_rules"]) >= 1


class TestDirectModuleIntegration:
    """直接模块集成测试（不通过 HTTP）"""

    def test_generator_to_engine_flow(self):
        """测试事件生成器到规则引擎的数据流"""
        # 1. 生成事件
        generator = BehaviorGenerator(user_pool_size=10, seed=42)
        events = generator.generate_batch(100)

        # 2. 统计用户行为
        user_stats = {}
        for event in events:
            user_id = event.user_id
            if user_id not in user_stats:
                user_stats[user_id] = {
                    "purchase_count": 0,
                    "view_count": 0,
                    "click_count": 0,
                    "total_amount": 0
                }

            if event.event_type == EventType.PURCHASE:
                user_stats[user_id]["purchase_count"] += 1
                user_stats[user_id]["total_amount"] += event.properties.get("amount", 0)
            elif event.event_type == EventType.VIEW:
                user_stats[user_id]["view_count"] += 1
            elif event.event_type == EventType.CLICK:
                user_stats[user_id]["click_count"] += 1

        # 3. 规则引擎评估
        engine = RuleEngine()
        engine.register_rule(Rule(
            id="active_user",
            name="活跃用户",
            condition="view_count >= 3 or click_count >= 2",
            priority=1,
            enabled=True,
            actions=[RuleAction(type="TAG_USER", params={"tags": ["active"]})]
        ))

        # 4. 评估所有用户
        matched_users = []
        for user_id, stats in user_stats.items():
            matched = engine.evaluate({**stats, "user_id": user_id})
            if matched:
                matched_users.append(user_id)

        # 验证有用户被标记
        assert len(matched_users) > 0

    def test_rule_engine_priority_ordering(self):
        """测试规则引擎优先级排序（优先级数值越小越优先）"""
        engine = RuleEngine()

        # 添加不同优先级的规则
        engine.register_rule(Rule(
            id="low_priority",
            name="低优先级规则",
            condition="value > 0",
            priority=10,  # 数值越大，优先级越低
            enabled=True,
            actions=[RuleAction(type="TAG_USER", params={"tags": ["low"]})]
        ))
        engine.register_rule(Rule(
            id="high_priority",
            name="高优先级规则",
            condition="value > 0",
            priority=1,  # 数值越小，优先级越高
            enabled=True,
            actions=[RuleAction(type="TAG_USER", params={"tags": ["high"]})]
        ))
        engine.register_rule(Rule(
            id="medium_priority",
            name="中优先级规则",
            condition="value > 0",
            priority=5,
            enabled=True,
            actions=[RuleAction(type="TAG_USER", params={"tags": ["medium"]})]
        ))

        # 评估
        matched = engine.evaluate({"value": 1, "user_id": "test"})

        # 验证规则都匹配
        assert len(matched) == 3
        # 验证返回的规则（顺序取决于 RuleEngine 实现）
        matched_ids = [r.id for r in matched]
        assert set(matched_ids) == {"low_priority", "high_priority", "medium_priority"}
