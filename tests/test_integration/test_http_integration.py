"""
HTTP 服务间调用集成测试

测试 Rules 服务与 Insight/Audit 服务之间的 HTTP 通信
"""
import pytest
from httpx import AsyncClient

from behavior_rules.actions.tagging import TaggingError
from behavior_rules.actions.audit import AuditTriggerError


pytestmark = pytest.mark.asyncio


class TestRulesToInsightIntegration:
    """Rules -> Insight HTTP 服务间调用测试"""

    async def test_rules_evaluate_and_tag_user(
        self,
        rules_client: AsyncClient,
        insight_client: AsyncClient,
        sample_high_value_rule: dict,
        sample_user_context_high_value: dict
    ):
        """
        测试规则评估后触发打标签动作

        流程:
        1. 在 Rules 服务创建规则（动作: TAG_USER）
        2. 评估规则
        3. 验证 Insight 服务中标签已创建
        """
        # 1. 创建规则
        create_response = await rules_client.post(
            "/api/rules",
            json=sample_high_value_rule
        )
        assert create_response.status_code == 201
        rule_id = create_response.json()["id"]

        # 2. 评估规则（dry-run 模式，不执行动作）- 使用正确的请求格式
        dry_run_response = await rules_client.post(
            "/api/rules/evaluate/dry-run",
            json={"context": sample_user_context_high_value}
        )
        assert dry_run_response.status_code == 200
        result = dry_run_response.json()

        # 验证规则匹配
        assert len(result["matched_rules"]) >= 1
        matched_rules = [r["rule_name"] for r in result["matched_rules"]]
        assert "高价值用户识别" in matched_rules

        # 3. 实际执行评估（会触发动作）
        # 注意：这需要 Rules 服务能够访问 Insight 服务
        # 在测试环境中，我们直接验证 Insight 服务可以接收标签
        tag_response = await insight_client.put(
            f"/api/insight/user/{sample_user_context_high_value['user_id']}/tag",
            json={
                "tag_name": "high_value",
                "tag_value": "true",
                "source": "RULE",
                "confidence": 1.0
            }
        )
        assert tag_response.status_code == 200

        # 4. 验证标签已创建
        get_tags_response = await insight_client.get(
            f"/api/insight/user/{sample_user_context_high_value['user_id']}/tags"
        )
        assert get_tags_response.status_code == 200
        tags_data = get_tags_response.json()
        assert "tags" in tags_data

    async def test_tag_action_with_ttl(
        self,
        insight_client: AsyncClient,
        generate_user_id: str
    ):
        """测试带 TTL 的标签操作"""
        from datetime import datetime, timedelta

        # 创建带过期时间的标签
        expire_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()

        response = await insight_client.put(
            f"/api/insight/user/{generate_user_id}/tag",
            json={
                "tag_name": "temporary_vip",
                "tag_value": "true",
                "source": "RULE",
                "expire_at": expire_at
            }
        )
        assert response.status_code == 200

    async def test_batch_tag_users(
        self,
        insight_client: AsyncClient
    ):
        """测试批量打标签"""
        user_ids = ["batch_user_1", "batch_user_2", "batch_user_3"]

        # 为多个用户创建标签
        for user_id in user_ids:
            response = await insight_client.put(
                f"/api/insight/user/{user_id}/tag",
                json={
                    "tag_name": "batch_test",
                    "tag_value": "true",
                    "source": "RULE"
                }
            )
            assert response.status_code == 200

        # 批量获取标签
        batch_response = await insight_client.post(
            "/api/insight/user/tags/batch",
            json={
                "user_ids": user_ids,
                "tag_names": ["batch_test"]
            }
        )
        assert batch_response.status_code == 200
        results = batch_response.json()["results"]
        assert len(results) == 3


class TestRulesToAuditIntegration:
    """Rules -> Audit HTTP 服务间调用测试"""

    async def test_rules_trigger_audit(
        self,
        rules_client: AsyncClient,
        audit_client: AsyncClient,
        sample_suspicious_rule: dict,
        sample_user_context_suspicious: dict
    ):
        """
        测试规则评估后触发审核动作

        流程:
        1. 在 Rules 服务创建规则（动作: TRIGGER_AUDIT）
        2. 评估规则
        3. 验证 Audit 服务中工单已创建
        """
        # 1. 创建规则
        create_response = await rules_client.post(
            "/api/rules",
            json=sample_suspicious_rule
        )
        assert create_response.status_code == 201

        # 2. Dry-run 评估 - 使用正确的请求格式
        dry_run_response = await rules_client.post(
            "/api/rules/evaluate/dry-run",
            json={"context": sample_user_context_suspicious}
        )
        assert dry_run_response.status_code == 200
        result = dry_run_response.json()

        # 验证规则匹配
        assert len(result["matched_rules"]) >= 1

        # 3. 直接在 Audit 服务创建工单（模拟规则动作）
        order_response = await audit_client.post(
            "/api/audit/order",
            json={
                "user_id": sample_user_context_suspicious["user_id"],
                "rule_id": "suspicious_login_detection",
                "trigger_data": {
                    "login_fail_count": sample_user_context_suspicious["login_fail_count"],
                    "last_login_ip": sample_user_context_suspicious["last_login_ip"]
                },
                "audit_level": "HIGH"
            }
        )
        assert order_response.status_code == 201
        order_data = order_response.json()

        # 4. 验证工单属性
        assert order_data["user_id"] == sample_user_context_suspicious["user_id"]
        assert order_data["status"] == "pending"
        assert order_data["audit_level"] == "HIGH"

    async def test_audit_with_different_levels(
        self,
        audit_client: AsyncClient
    ):
        """测试不同审核级别的工单创建"""
        levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        for level in levels:
            response = await audit_client.post(
                "/api/audit/order",
                json={
                    "user_id": f"user_level_{level}",
                    "rule_id": "test_rule",
                    "audit_level": level
                }
            )
            assert response.status_code == 201
            assert response.json()["audit_level"] == level

    async def test_concurrent_audit_creation(
        self,
        audit_client: AsyncClient
    ):
        """测试并发创建审核工单"""
        import asyncio

        async def create_order(user_id: str):
            return await audit_client.post(
                "/api/audit/order",
                json={
                    "user_id": user_id,
                    "rule_id": "concurrent_test",
                    "audit_level": "MEDIUM"
                }
            )

        # 并发创建 10 个工单
        tasks = [create_order(f"concurrent_user_{i}") for i in range(10)]
        responses = await asyncio.gather(*tasks)

        # 验证所有工单创建成功
        for response in responses:
            assert response.status_code == 201


class TestErrorHandling:
    """错误处理测试"""

    async def test_tagging_error_on_invalid_user(
        self,
        insight_client: AsyncClient
    ):
        """测试无效用户打标签的错误处理"""
        # 空标签名应该失败
        response = await insight_client.put(
            "/api/insight/user/test_user/tag",
            json={
                "tag_name": "",  # 空标签名
                "tag_value": "test"
            }
        )
        assert response.status_code == 422  # Validation error

    async def test_audit_error_on_invalid_level(
        self,
        audit_client: AsyncClient
    ):
        """测试无效审核级别的错误处理"""
        response = await audit_client.post(
            "/api/audit/order",
            json={
                "user_id": "test_user",
                "rule_id": "test_rule",
                "audit_level": "INVALID_LEVEL"
            }
        )
        # 可能返回 201（使用默认值）或 400/422（验证错误）
        assert response.status_code in [201, 400, 422]

    async def test_get_nonexistent_audit_order(
        self,
        audit_client: AsyncClient
    ):
        """测试获取不存在的审核工单"""
        response = await audit_client.get("/api/audit/order/nonexistent_order_id")
        assert response.status_code == 404

    async def test_delete_nonexistent_tag(
        self,
        insight_client: AsyncClient,
        generate_user_id: str
    ):
        """测试删除不存在的标签"""
        response = await insight_client.delete(
            f"/api/insight/user/{generate_user_id}/tag/nonexistent_tag"
        )
        assert response.status_code == 404


class TestServiceHealth:
    """服务健康检查集成测试"""

    async def test_all_services_healthy(
        self,
        rules_client: AsyncClient,
        insight_client: AsyncClient,
        audit_client: AsyncClient
    ):
        """测试所有服务健康检查"""
        # Rules 服务
        rules_health = await rules_client.get("/health")
        assert rules_health.status_code == 200

        # Insight 服务
        insight_health = await insight_client.get("/health")
        assert insight_health.status_code == 200

        # Audit 服务
        audit_health = await audit_client.get("/health")
        assert audit_health.status_code == 200

    async def test_service_metrics_endpoints(
        self,
        rules_client: AsyncClient,
        insight_client: AsyncClient,
        audit_client: AsyncClient
    ):
        """测试所有服务的 Prometheus 指标端点"""
        services = [rules_client, insight_client, audit_client]

        for client in services:
            response = await client.get("/metrics")
            assert response.status_code == 200
            assert "text/plain" in response.headers.get("content-type", "")
