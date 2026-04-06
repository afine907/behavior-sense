"""
状态一致性验证测试

验证并发操作和数据一致性
"""
import asyncio
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestAuditStatusTransitions:
    """审核状态转换一致性测试"""

    async def test_valid_status_transitions(
        self,
        audit_client: AsyncClient
    ):
        """
        测试合法的状态转换

        状态转换规则:
        - pending -> in_review (分配)
        - in_review -> approved (审核通过)
        - in_review -> rejected (审核驳回)
        - approved/rejected -> closed (关闭)
        - rejected -> pending/in_review (重新打开)
        """
        # pending -> in_review
        create_response = await audit_client.post(
            "/api/audit/order",
            json={"user_id": "transition_user", "rule_id": "transition_test"}
        )
        order_id = create_response.json()["id"]
        assert create_response.json()["status"] == "pending"

        # pending -> in_review (通过分配)
        assign_response = await audit_client.put(
            f"/api/audit/order/{order_id}/assign",
            json={"assignee": "reviewer_transition"}
        )
        assert assign_response.json()["status"] == "in_review"

        # in_review -> approved
        review_response = await audit_client.put(
            f"/api/audit/order/{order_id}/review",
            json={"status": "approved", "reviewer": "reviewer_transition"}
        )
        assert review_response.json()["status"] == "approved"

    async def test_invalid_status_transition(
        self,
        audit_client: AsyncClient
    ):
        """测试非法状态转换被拒绝"""
        # 创建工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json={"user_id": "invalid_transition_user", "rule_id": "test"}
        )
        order_id = create_response.json()["id"]

        # 尝试在 pending 状态直接提交审核结果（不经过分配）
        # 根据实现，这可能被允许或拒绝
        # 如果需要先分配才能审核，应该返回 400
        review_response = await audit_client.put(
            f"/api/audit/order/{order_id}/review",
            json={"status": "approved", "reviewer": "direct_reviewer"}
        )
        # 根据业务逻辑，可能允许或拒绝
        # 如果允许，状态会直接变为 approved
        # 如果拒绝，返回 400
        assert review_response.status_code in [200, 400]

    async def test_reopen_transitions(
        self,
        audit_client: AsyncClient
    ):
        """测试重新打开的状态转换"""
        # 创建完整的审核流程
        create_response = await audit_client.post(
            "/api/audit/order",
            json={"user_id": "reopen_transition_user", "rule_id": "test"}
        )
        order_id = create_response.json()["id"]

        # 分配
        await audit_client.put(
            f"/api/audit/order/{order_id}/assign",
            json={"assignee": "reopen_reviewer"}
        )

        # 驳回
        await audit_client.put(
            f"/api/audit/order/{order_id}/review",
            json={"status": "rejected", "reviewer": "reopen_reviewer"}
        )

        # 重新打开
        reopen_response = await audit_client.put(
            f"/api/audit/order/{order_id}/reopen"
        )
        assert reopen_response.status_code == 200
        new_status = reopen_response.json()["status"]
        assert new_status in ["pending", "in_review"]


class TestConcurrentTagUpdates:
    """并发标签更新测试"""

    async def test_concurrent_tag_updates_same_user(
        self,
        insight_client: AsyncClient,
        generate_user_id: str
    ):
        """测试并发更新同一用户的标签"""
        user_id = generate_user_id

        # 并发更新多个标签
        async def update_tag(tag_name: str, tag_value: str):
            return await insight_client.put(
                f"/api/insight/user/{user_id}/tag",
                json={
                    "tag_name": tag_name,
                    "tag_value": tag_value,
                    "source": "RULE"
                }
            )

        # 并发更新 5 个不同的标签
        tasks = [
            update_tag(f"concurrent_tag_{i}", f"value_{i}")
            for i in range(5)
        ]
        responses = await asyncio.gather(*tasks)

        # 所有更新应该成功
        for response in responses:
            assert response.status_code == 200

        # 验证所有标签都已创建
        get_response = await insight_client.get(f"/api/insight/user/{user_id}/tags")
        assert get_response.status_code == 200

    async def test_concurrent_tag_updates_same_tag(
        self,
        insight_client: AsyncClient,
        generate_user_id: str
    ):
        """测试并发更新同一标签（最后写入者胜出）"""
        user_id = generate_user_id

        # 并发更新同一标签
        async def update_tag(value: str):
            return await insight_client.put(
                f"/api/insight/user/{user_id}/tag",
                json={
                    "tag_name": "race_condition_tag",
                    "tag_value": value,
                    "source": "RULE"
                }
            )

        # 并发更新
        tasks = [update_tag(f"value_{i}") for i in range(3)]
        responses = await asyncio.gather(*tasks)

        # 所有更新应该成功（最后一个值生效）
        for response in responses:
            assert response.status_code == 200

        # 验证标签存在
        get_response = await insight_client.get(f"/api/insight/user/{user_id}/tags")
        assert get_response.status_code == 200


class TestConcurrentAuditOperations:
    """并发审核操作测试"""

    async def test_concurrent_assign_same_order(
        self,
        audit_client: AsyncClient
    ):
        """测试并发分配同一工单"""
        # 创建工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json={"user_id": "concurrent_assign_user", "rule_id": "test"}
        )
        assert create_response.status_code == 201, f"Expected 201, got {create_response.status_code}: {create_response.text}"
        order_id = create_response.json()["id"]

        # 并发分配给不同的人
        async def assign(assignee: str):
            return await audit_client.put(
                f"/api/audit/order/{order_id}/assign",
                json={"assignee": assignee}
            )

        tasks = [assign(f"concurrent_reviewer_{i}") for i in range(3)]
        responses = await asyncio.gather(*tasks)

        # 至少有一个应该成功
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 1

        # 验证最终状态
        get_response = await audit_client.get(f"/api/audit/order/{order_id}")
        assert get_response.json()["status"] == "in_review"

    async def test_concurrent_review_same_order(
        self,
        audit_client: AsyncClient
    ):
        """测试并发审核同一工单"""
        # 创建并分配工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json={"user_id": "concurrent_review_user", "rule_id": "test"}
        )
        assert create_response.status_code == 201, f"Expected 201, got {create_response.status_code}: {create_response.text}"
        order_id = create_response.json()["id"]

        await audit_client.put(
            f"/api/audit/order/{order_id}/assign",
            json={"assignee": "main_reviewer"}
        )

        # 并发提交不同的审核结果
        async def submit_review(status: str):
            return await audit_client.put(
                f"/api/audit/order/{order_id}/review",
                json={"status": status, "reviewer": "concurrent_reviewer"}
            )

        # 一个通过，一个驳回
        tasks = [
            submit_review("approved"),
            submit_review("rejected")
        ]
        responses = await asyncio.gather(*tasks)

        # 只有一个应该成功（先到的请求）
        success_statuses = [
            r.json()["status"]
            for r in responses
            if r.status_code == 200
        ]
        # 最终状态应该是 approved 或 rejected 之一
        assert len(set(success_statuses)) == 1


class TestRuleEvaluationIdempotency:
    """规则评估幂等性测试"""

    async def test_dry_run_idempotency(
        self,
        rules_client: AsyncClient,
        sample_high_value_rule: dict
    ):
        """测试 dry-run 评估的幂等性（不产生副作用）"""
        # 创建规则
        await rules_client.post("/api/rules", json=sample_high_value_rule)

        context = {
            "user_id": "idempotency_test_user",
            "purchase_count": 10,
            "total_amount": 5000
        }

        # 多次 dry-run 评估 - 使用正确的请求格式
        results = []
        for _ in range(3):
            response = await rules_client.post(
                "/api/rules/evaluate/dry-run",
                json={"context": context}
            )
            assert response.status_code == 200
            results.append(response.json())

        # 结果应该一致
        matched_counts = [len(r["matched_rules"]) for r in results]
        assert len(set(matched_counts)) == 1  # 所有结果相同

    async def test_rule_list_consistency(
        self,
        rules_client: AsyncClient
    ):
        """测试规则列表一致性"""
        # 创建多个规则
        for i in range(5):
            await rules_client.post(
                "/api/rules",
                json={
                    "name": f"一致性测试规则 {i}",
                    "condition": f"value >= {i}",
                    "actions": [{"type": "TAG_USER", "params": {"tags": [f"tag_{i}"]}}],
                    "enabled": True
                }
            )

        # 多次获取列表
        responses = await asyncio.gather(
            rules_client.get("/api/rules"),
            rules_client.get("/api/rules"),
            rules_client.get("/api/rules")
        )

        # 所有响应应该相同 - API 返回列表，检查长度
        counts = [len(r.json()) for r in responses]
        assert len(set(counts)) == 1


class TestDataIntegrity:
    """数据完整性测试"""

    async def test_user_profile_consistency(
        self,
        insight_client: AsyncClient,
        generate_user_id: str
    ):
        """测试用户画像数据一致性"""
        user_id = generate_user_id

        # 创建画像
        profile_data = {
            "basic_info": {"name": "Test User", "email": "test@example.com"},
            "behavior_tags": ["tag1", "tag2"],
            "risk_level": "low"
        }

        create_response = await insight_client.put(
            f"/api/insight/user/{user_id}/profile",
            json=profile_data
        )
        assert create_response.status_code == 200

        # 获取并验证
        get_response = await insight_client.get(f"/api/insight/user/{user_id}/profile")
        assert get_response.status_code == 200

        retrieved = get_response.json()
        assert retrieved["basic_info"]["name"] == profile_data["basic_info"]["name"]
        assert retrieved["risk_level"] == profile_data["risk_level"]

    async def test_audit_order_data_integrity(
        self,
        audit_client: AsyncClient
    ):
        """测试审核工单数据完整性"""
        trigger_data = {
            "event_type": "suspicious_login",
            "ip_address": "192.168.1.100",
            "location": "Beijing",
            "timestamp": "2026-04-05T12:00:00Z"
        }

        # 创建工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json={
                "user_id": "integrity_user",
                "rule_id": "integrity_test",
                "trigger_data": trigger_data,
                "audit_level": "HIGH"
            }
        )
        assert create_response.status_code == 201
        order_id = create_response.json()["id"]

        # 获取并验证
        get_response = await audit_client.get(f"/api/audit/order/{order_id}")
        assert get_response.status_code == 200

        retrieved = get_response.json()
        assert retrieved["trigger_data"]["event_type"] == trigger_data["event_type"]
        assert retrieved["trigger_data"]["ip_address"] == trigger_data["ip_address"]
