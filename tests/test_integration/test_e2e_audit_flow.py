"""
端到端：审核流程测试

测试从规则触发到审核完成的完整业务流程
"""
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestAuditFlow:
    """审核流程端到端测试"""

    async def test_complete_audit_flow(
        self,
        multi_service_context,
        sample_suspicious_rule: dict,
        sample_user_context_suspicious: dict
    ):
        """
        完整的审核流程测试

        流程:
        1. 创建可疑行为检测规则
        2. 评估规则
        3. 创建审核工单
        4. 分配审核人
        5. 提交审核结果
        6. 验证状态转换
        """
        rules = multi_service_context.rules
        audit = multi_service_context.audit
        user_id = sample_user_context_suspicious["user_id"]

        # Step 1: 创建规则
        create_rule_response = await rules.post(
            "/api/rules",
            json=sample_suspicious_rule
        )
        assert create_rule_response.status_code == 201
        rule_id = create_rule_response.json()["id"]

        # Step 2: 评估规则（dry-run）
        dry_run_response = await rules.post(
            "/api/rules/evaluate/dry-run",
            json=sample_user_context_suspicious
        )
        assert dry_run_response.status_code == 200
        assert dry_run_response.json()["matched_count"] >= 1

        # Step 3: 创建审核工单
        create_order_response = await audit.post(
            "/api/audit/order",
            json={
                "user_id": user_id,
                "rule_id": rule_id,
                "trigger_data": {
                    "login_fail_count": sample_user_context_suspicious["login_fail_count"],
                    "detection_type": "brute_force"
                },
                "audit_level": "HIGH"
            }
        )
        assert create_order_response.status_code == 201
        order_data = create_order_response.json()
        order_id = order_data["id"]

        # 验证初始状态
        assert order_data["status"] == "pending"
        assert order_data["audit_level"] == "HIGH"

        # Step 4: 获取工单详情
        get_order_response = await audit.get(f"/api/audit/order/{order_id}")
        assert get_order_response.status_code == 200
        assert get_order_response.json()["user_id"] == user_id

        # Step 5: 分配审核人
        assign_response = await audit.put(
            f"/api/audit/order/{order_id}/assign",
            json={"assignee": "reviewer_001"}
        )
        assert assign_response.status_code == 200
        assigned_order = assign_response.json()

        # 验证状态转换: pending -> in_review
        assert assigned_order["status"] == "in_review"
        assert assigned_order["assignee"] == "reviewer_001"

        # Step 6: 提交审核结果（通过）
        review_response = await audit.put(
            f"/api/audit/order/{order_id}/review",
            json={
                "status": "approved",
                "note": "用户行为正常，误报",
                "reviewer": "reviewer_001"
            }
        )
        assert review_response.status_code == 200
        reviewed_order = review_response.json()

        # 验证最终状态
        assert reviewed_order["status"] == "approved"

    async def test_audit_rejection_flow(
        self,
        audit_client: AsyncClient
    ):
        """测试审核驳回流程"""
        # 创建工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json={
                "user_id": "rejection_test_user",
                "rule_id": "test_rule",
                "audit_level": "MEDIUM"
            }
        )
        assert create_response.status_code == 201
        order_id = create_response.json()["id"]

        # 分配
        await audit_client.put(
            f"/api/audit/order/{order_id}/assign",
            json={"assignee": "reviewer_reject"}
        )

        # 驳回
        reject_response = await audit_client.put(
            f"/api/audit/order/{order_id}/review",
            json={
                "status": "rejected",
                "note": "确认异常行为，需要进一步调查",
                "reviewer": "reviewer_reject"
            }
        )
        assert reject_response.status_code == 200
        assert reject_response.json()["status"] == "rejected"

    async def test_audit_reopen_flow(
        self,
        audit_client: AsyncClient
    ):
        """测试工单重新打开流程"""
        # 创建并完成工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json={
                "user_id": "reopen_test_user",
                "rule_id": "test_rule",
                "audit_level": "LOW"
            }
        )
        order_id = create_response.json()["id"]

        # 分配并驳回
        await audit_client.put(
            f"/api/audit/order/{order_id}/assign",
            json={"assignee": "reviewer_reopen"}
        )
        await audit_client.put(
            f"/api/audit/order/{order_id}/review",
            json={"status": "rejected", "reviewer": "reviewer_reopen"}
        )

        # 重新打开
        reopen_response = await audit_client.put(
            f"/api/audit/order/{order_id}/reopen"
        )
        assert reopen_response.status_code == 200
        # 重新打开后状态应该是 pending 或 in_review
        assert reopen_response.json()["status"] in ["pending", "in_review"]


class TestAuditListOperations:
    """审核列表操作测试"""

    async def test_list_orders_with_pagination(
        self,
        audit_client: AsyncClient
    ):
        """测试分页获取工单列表"""
        # 创建多个工单
        for i in range(5):
            await audit_client.post(
                "/api/audit/order",
                json={
                    "user_id": f"list_user_{i}",
                    "rule_id": "list_test_rule",
                    "audit_level": "MEDIUM"
                }
            )

        # 获取第一页
        page1_response = await audit_client.get(
            "/api/audit/orders?page=1&size=2"
        )
        assert page1_response.status_code == 200
        page1_data = page1_response.json()

        assert page1_data["page"] == 1
        assert page1_data["size"] == 2
        assert len(page1_data["items"]) <= 2
        assert page1_data["total"] >= 5

    async def test_filter_by_status(
        self,
        audit_client: AsyncClient
    ):
        """测试按状态过滤工单"""
        # 创建工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json={
                "user_id": "filter_status_user",
                "rule_id": "filter_test",
                "audit_level": "MEDIUM"
            }
        )
        order_id = create_response.json()["id"]

        # 分配使其变为 in_review
        await audit_client.put(
            f"/api/audit/order/{order_id}/assign",
            json={"assignee": "filter_reviewer"}
        )

        # 过滤 in_review 状态
        filter_response = await audit_client.get(
            "/api/audit/orders?status=in_review"
        )
        assert filter_response.status_code == 200
        items = filter_response.json()["items"]

        for item in items:
            assert item["status"] == "in_review"

    async def test_get_todo_list(
        self,
        audit_client: AsyncClient
    ):
        """测试获取待办列表"""
        # 创建并分配工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json={
                "user_id": "todo_user",
                "rule_id": "todo_test",
                "audit_level": "HIGH"
            }
        )
        order_id = create_response.json()["id"]

        await audit_client.put(
            f"/api/audit/order/{order_id}/assign",
            json={"assignee": "todo_reviewer"}
        )

        # 获取待办
        todo_response = await audit_client.get(
            "/api/audit/orders/todo?assignee=todo_reviewer"
        )
        assert todo_response.status_code == 200
        todo_items = todo_response.json()

        assert isinstance(todo_items, list)
        # 应该包含刚创建的工单
        todo_ids = [item["id"] for item in todo_items]
        assert order_id in todo_ids

    async def test_get_unassigned_orders(
        self,
        audit_client: AsyncClient
    ):
        """测试获取未分配工单"""
        # 创建未分配的工单
        await audit_client.post(
            "/api/audit/order",
            json={
                "user_id": "unassigned_user",
                "rule_id": "unassigned_test",
                "audit_level": "LOW"
            }
        )

        # 获取未分配列表
        unassigned_response = await audit_client.get(
            "/api/audit/orders/unassigned"
        )
        assert unassigned_response.status_code == 200
        unassigned_items = unassigned_response.json()

        assert isinstance(unassigned_items, list)
        for item in unassigned_items:
            assert item["assignee"] is None


class TestBatchAuditOperations:
    """批量审核操作测试"""

    async def test_batch_assign(
        self,
        audit_client: AsyncClient
    ):
        """测试批量分配审核人"""
        # 创建多个工单
        order_ids = []
        for i in range(3):
            response = await audit_client.post(
                "/api/audit/order",
                json={
                    "user_id": f"batch_user_{i}",
                    "rule_id": "batch_assign_test",
                    "audit_level": "MEDIUM"
                }
            )
            order_ids.append(response.json()["id"])

        # 批量分配
        batch_response = await audit_client.post(
            "/api/audit/orders/batch-assign",
            json={
                "order_ids": order_ids,
                "assignee": "batch_reviewer"
            }
        )
        assert batch_response.status_code == 200
        results = batch_response.json()

        assert len(results) == 3
        for result in results:
            assert result["assignee"] == "batch_reviewer"
            assert result["status"] == "in_review"


class TestAuditStatistics:
    """审核统计测试"""

    async def test_get_audit_stats(
        self,
        audit_client: AsyncClient
    ):
        """测试获取审核统计"""
        # 创建一些工单
        await audit_client.post(
            "/api/audit/order",
            json={
                "user_id": "stats_user",
                "rule_id": "stats_test",
                "audit_level": "HIGH"
            }
        )

        # 获取统计
        stats_response = await audit_client.get("/api/audit/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()

        assert "status_counts" in stats
        assert "level_counts" in stats
        assert "today_count" in stats

        # 验证统计格式
        assert isinstance(stats["status_counts"], dict)
        assert isinstance(stats["level_counts"], dict)
        assert isinstance(stats["today_count"], int)
