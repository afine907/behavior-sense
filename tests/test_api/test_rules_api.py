"""
Rules 服务 API 接口测试
"""
import pytest
from httpx import AsyncClient


class TestRulesHealth:
    """Rules 服务健康检查测试"""

    @pytest.mark.asyncio
    async def test_health_check(self, rules_client: AsyncClient):
        """测试健康检查接口"""
        response = await rules_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "behavior-rules"
        assert "rules_count" in data
        assert "handlers_count" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_readiness_check(self, rules_client: AsyncClient):
        """测试就绪检查接口"""
        response = await rules_client.get("/ready")

        assert response.status_code == 200
        data = response.json()

        assert data["ready"] is True
        assert data["service"] == "behavior-rules"

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, rules_client: AsyncClient):
        """测试 Prometheus 指标接口"""
        response = await rules_client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


class TestRulesCRUD:
    """Rules 服务 CRUD 测试"""

    @pytest.mark.asyncio
    async def test_list_rules_empty(self, rules_client: AsyncClient):
        """测试空规则列表"""
        response = await rules_client.get("/api/rules")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_create_rule(self, rules_client: AsyncClient, sample_rule_create: dict):
        """测试创建规则"""
        response = await rules_client.post("/api/rules", json=sample_rule_create)

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == sample_rule_create["name"]
        assert data["condition"] == sample_rule_create["condition"]
        assert data["enabled"] is True
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_rule_minimal(self, rules_client: AsyncClient):
        """测试创建最小规则"""
        response = await rules_client.post(
            "/api/rules",
            json={
                "name": "简单规则",
                "condition": "value > 10"
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == "简单规则"
        assert data["priority"] == 0  # 默认优先级

    @pytest.mark.asyncio
    async def test_create_rule_invalid(self, rules_client: AsyncClient):
        """测试创建无效规则"""
        response = await rules_client.post(
            "/api/rules",
            json={
                "name": "无效规则"
                # 缺少 condition
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_rule(self, rules_client: AsyncClient, sample_rule_create: dict):
        """测试获取规则详情"""
        # 先创建规则
        create_response = await rules_client.post("/api/rules", json=sample_rule_create)
        rule_id = create_response.json()["id"]

        # 获取规则
        response = await rules_client.get(f"/api/rules/{rule_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == rule_id
        assert data["name"] == sample_rule_create["name"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_rule(self, rules_client: AsyncClient):
        """测试获取不存在的规则"""
        response = await rules_client.get("/api/rules/nonexistent_rule_id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_rule(self, rules_client: AsyncClient, sample_rule_create: dict):
        """测试更新规则"""
        # 创建规则
        create_response = await rules_client.post("/api/rules", json=sample_rule_create)
        rule_id = create_response.json()["id"]

        # 更新规则
        update_data = {
            "name": "更新后的规则名",
            "description": "更新后的描述",
            "priority": 10
        }
        response = await rules_client.put(f"/api/rules/{rule_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["priority"] == update_data["priority"]
        assert data["version"] == 2  # 版本递增

    @pytest.mark.asyncio
    async def test_update_nonexistent_rule(self, rules_client: AsyncClient):
        """测试更新不存在的规则"""
        response = await rules_client.put(
            "/api/rules/nonexistent_rule_id",
            json={"name": "更新"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_rule(self, rules_client: AsyncClient, sample_rule_create: dict):
        """测试删除规则"""
        # 创建规则
        create_response = await rules_client.post("/api/rules", json=sample_rule_create)
        rule_id = create_response.json()["id"]

        # 删除规则
        response = await rules_client.delete(f"/api/rules/{rule_id}")

        assert response.status_code == 204

        # 验证已删除
        get_response = await rules_client.get(f"/api/rules/{rule_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_rule(self, rules_client: AsyncClient):
        """测试删除不存在的规则"""
        response = await rules_client.delete("/api/rules/nonexistent_rule_id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_rules_with_pagination(self, rules_client: AsyncClient):
        """测试规则列表分页"""
        # 创建多个规则
        for i in range(5):
            await rules_client.post(
                "/api/rules",
                json={
                    "name": f"规则{i}",
                    "condition": f"value > {i}"
                }
            )

        # 测试分页
        response = await rules_client.get("/api/rules?limit=2&offset=0")

        assert response.status_code == 200
        data = response.json()

        assert len(data) <= 2

    @pytest.mark.asyncio
    async def test_list_rules_filter_enabled(self, rules_client: AsyncClient):
        """测试按启用状态过滤规则"""
        # 创建启用和禁用的规则
        await rules_client.post(
            "/api/rules",
            json={"name": "启用规则", "condition": "1==1", "enabled": True}
        )
        await rules_client.post(
            "/api/rules",
            json={"name": "禁用规则", "condition": "1==1", "enabled": False}
        )

        # 过滤只获取启用的
        response = await rules_client.get("/api/rules?enabled=true")

        assert response.status_code == 200
        data = response.json()

        for rule in data:
            assert rule["enabled"] is True

    @pytest.mark.asyncio
    async def test_list_rules_filter_tag(self, rules_client: AsyncClient):
        """测试按标签过滤规则"""
        # 创建带标签的规则
        await rules_client.post(
            "/api/rules",
            json={
                "name": "带标签规则",
                "condition": "1==1",
                "tags": ["marketing", "vip"]
            }
        )

        # 按标签过滤
        response = await rules_client.get("/api/rules?tag=marketing")

        assert response.status_code == 200
        data = response.json()

        for rule in data:
            assert "marketing" in rule["tags"]


class TestRulesEvaluation:
    """Rules 服务评估测试"""

    @pytest.mark.asyncio
    async def test_evaluate_rules(self, rules_client: AsyncClient, sample_context: dict):
        """测试规则评估"""
        # 创建规则
        await rules_client.post(
            "/api/rules",
            json={
                "name": "高价值用户",
                "condition": "purchase_count >= 5",
                "priority": 1,
                "enabled": True
            }
        )

        # 评估
        response = await rules_client.post(
            "/api/rules/evaluate",
            json={
                "context": sample_context,
                "execute_actions": False
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "matched_rules" in data
        assert "total_rules_evaluated" in data
        assert "execution_time_ms" in data

    @pytest.mark.asyncio
    async def test_evaluate_specific_rules(
        self, rules_client: AsyncClient, sample_context: dict
    ):
        """测试评估指定规则"""
        # 创建多个规则
        create_response = await rules_client.post(
            "/api/rules",
            json={
                "name": "指定评估规则",
                "condition": "purchase_count >= 5",
                "priority": 1
            }
        )
        rule_id = create_response.json()["id"]

        # 评估指定规则
        response = await rules_client.post(
            "/api/rules/evaluate",
            json={
                "context": sample_context,
                "rule_ids": [rule_id],
                "execute_actions": False
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_rules_evaluated"] == 1

    @pytest.mark.asyncio
    async def test_dry_run_evaluate(self, rules_client: AsyncClient, sample_context: dict):
        """测试演练评估（不执行动作）"""
        # 创建带动作的规则
        await rules_client.post(
            "/api/rules",
            json={
                "name": "带动作规则",
                "condition": "purchase_count >= 5",
                "actions": [
                    {
                        "type": "TAG_USER",
                        "params": {"tags": ["high_value"]}
                    }
                ]
            }
        )

        # 演练评估
        response = await rules_client.post(
            "/api/rules/evaluate/dry-run",
            json={"context": sample_context}
        )

        assert response.status_code == 200
        data = response.json()

        # 演练模式下不应该执行动作
        for result in data["matched_rules"]:
            assert result["actions_executed"] == []

    @pytest.mark.asyncio
    async def test_validate_rule_condition(self, rules_client: AsyncClient):
        """测试规则条件验证"""
        # 有效条件
        response = await rules_client.post(
            "/api/rules/validate",
            json={
                "name": "验证规则",
                "condition": "purchase_count >= 5 and total_amount > 1000"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_invalid_condition(self, rules_client: AsyncClient):
        """测试无效条件验证"""
        response = await rules_client.post(
            "/api/rules/validate",
            json={
                "name": "无效规则",
                "condition": "invalid syntax >>> 5"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert "error" in data


class TestRulesStatistics:
    """Rules 服务统计测试"""

    @pytest.mark.asyncio
    async def test_get_stats(self, rules_client: AsyncClient):
        """测试获取统计信息"""
        # 创建一些规则
        await rules_client.post(
            "/api/rules",
            json={"name": "规则1", "condition": "1==1", "enabled": True, "tags": ["a"]}
        )
        await rules_client.post(
            "/api/rules",
            json={"name": "规则2", "condition": "1==1", "enabled": False, "tags": ["b"]}
        )

        response = await rules_client.get("/api/rules/stats")

        assert response.status_code == 200
        data = response.json()

        assert "total_rules" in data
        assert "enabled_rules" in data
        assert "disabled_rules" in data
        assert "tags" in data
        assert "priority_distribution" in data
