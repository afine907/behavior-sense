"""
Audit 服务 API 接口测试
"""
import pytest
from httpx import AsyncClient


class TestAuditHealth:
    """Audit 服务健康检查测试"""

    @pytest.mark.asyncio
    async def test_health_check(self, audit_client: AsyncClient):
        """测试健康检查接口"""
        response = await audit_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "behavior_audit"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, audit_client: AsyncClient):
        """测试 Prometheus 指标接口"""
        response = await audit_client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_root_endpoint(self, audit_client: AsyncClient):
        """测试根路径"""
        response = await audit_client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "BehaviorSense Audit Service"
        assert "version" in data
        assert data["docs"] == "/docs"


class TestAuditOrder:
    """Audit 服务工单管理测试"""

    @pytest.mark.asyncio
    async def test_create_order(self, audit_client: AsyncClient, sample_order_create: dict):
        """测试创建审核工单"""
        response = await audit_client.post("/api/audit/order", json=sample_order_create)

        assert response.status_code == 201
        data = response.json()

        assert data["user_id"] == sample_order_create["user_id"]
        assert data["rule_id"] == sample_order_create["rule_id"]
        assert data["status"] == "pending"
        assert "id" in data
        assert "create_time" in data

    @pytest.mark.asyncio
    async def test_create_order_minimal(self, audit_client: AsyncClient):
        """测试创建最小工单"""
        response = await audit_client.post(
            "/api/audit/order",
            json={
                "user_id": "user_minimal",
                "rule_id": "rule_minimal"
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["audit_level"] == "medium"  # 默认级别

    @pytest.mark.asyncio
    async def test_create_order_invalid_level(self, audit_client: AsyncClient):
        """测试无效审核级别"""
        response = await audit_client.post(
            "/api/audit/order",
            json={
                "user_id": "user_test",
                "rule_id": "rule_test",
                "audit_level": "invalid_level"
            }
        )

        # 应该返回验证错误或使用默认值
        assert response.status_code in [201, 400, 422]

    @pytest.mark.asyncio
    async def test_get_order(self, audit_client: AsyncClient, sample_order_create: dict):
        """测试获取工单详情"""
        # 先创建工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json=sample_order_create
        )
        order_id = create_response.json()["id"]

        # 获取工单
        response = await audit_client.get(f"/api/audit/order/{order_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == order_id
        assert data["user_id"] == sample_order_create["user_id"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_order(self, audit_client: AsyncClient):
        """测试获取不存在的工单"""
        response = await audit_client.get("/api/audit/order/nonexistent_order_id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_assign_order(self, audit_client: AsyncClient, sample_order_create: dict):
        """测试分配审核人"""
        # 创建工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json=sample_order_create
        )
        order_id = create_response.json()["id"]

        # 分配审核人
        response = await audit_client.put(
            f"/api/audit/order/{order_id}/assign",
            json={"assignee": "reviewer_001"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["assignee"] == "reviewer_001"
        assert data["status"] == "in_review"

    @pytest.mark.asyncio
    async def test_assign_nonexistent_order(self, audit_client: AsyncClient):
        """测试分配不存在的工单"""
        response = await audit_client.put(
            "/api/audit/order/nonexistent_id/assign",
            json={"assignee": "reviewer_001"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_submit_review_approve(self, audit_client: AsyncClient, sample_order_create: dict):
        """测试审核通过"""
        # 创建并分配工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json=sample_order_create
        )
        order_id = create_response.json()["id"]

        await audit_client.put(
            f"/api/audit/order/{order_id}/assign",
            json={"assignee": "reviewer_001"}
        )

        # 提交审核
        response = await audit_client.put(
            f"/api/audit/order/{order_id}/review",
            json={
                "status": "approved",
                "note": "审核通过",
                "reviewer": "reviewer_001"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "approved"

    @pytest.mark.asyncio
    async def test_submit_review_reject(self, audit_client: AsyncClient, sample_order_create: dict):
        """测试审核驳回"""
        # 创建并分配工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json=sample_order_create
        )
        order_id = create_response.json()["id"]

        await audit_client.put(
            f"/api/audit/order/{order_id}/assign",
            json={"assignee": "reviewer_001"}
        )

        # 驳回
        response = await audit_client.put(
            f"/api/audit/order/{order_id}/review",
            json={
                "status": "rejected",
                "note": "行为异常，需要进一步调查",
                "reviewer": "reviewer_001"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_reopen_order(self, audit_client: AsyncClient, sample_order_create: dict):
        """测试重新打开工单"""
        # 创建完整流程
        create_response = await audit_client.post(
            "/api/audit/order",
            json=sample_order_create
        )
        order_id = create_response.json()["id"]

        await audit_client.put(
            f"/api/audit/order/{order_id}/assign",
            json={"assignee": "reviewer_001"}
        )

        await audit_client.put(
            f"/api/audit/order/{order_id}/review",
            json={"status": "rejected", "reviewer": "reviewer_001"}
        )

        # 重新打开
        response = await audit_client.put(
            f"/api/audit/order/{order_id}/reopen"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["pending", "in_review"]

    @pytest.mark.asyncio
    async def test_delete_order(self, audit_client: AsyncClient, sample_order_create: dict):
        """测试删除工单"""
        # 创建工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json=sample_order_create
        )
        order_id = create_response.json()["id"]

        # 删除工单
        response = await audit_client.delete(f"/api/audit/order/{order_id}")

        assert response.status_code == 204

        # 验证已删除
        get_response = await audit_client.get(f"/api/audit/order/{order_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_order(self, audit_client: AsyncClient):
        """测试删除不存在的工单"""
        response = await audit_client.delete("/api/audit/order/nonexistent_id")

        assert response.status_code == 404


class TestAuditList:
    """Audit 服务工单列表测试"""

    @pytest.mark.asyncio
    async def test_list_orders(self, audit_client: AsyncClient, sample_order_create: dict):
        """测试获取工单列表"""
        # 创建一些工单
        for i in range(3):
            await audit_client.post(
                "/api/audit/order",
                json={
                    **sample_order_create,
                    "user_id": f"user_{i}"
                }
            )

        response = await audit_client.get("/api/audit/orders")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

    @pytest.mark.asyncio
    async def test_list_orders_with_pagination(self, audit_client: AsyncClient, sample_order_create: dict):
        """测试工单列表分页"""
        # 创建多个工单
        for i in range(5):
            await audit_client.post(
                "/api/audit/order",
                json={**sample_order_create, "user_id": f"user_page_{i}"}
            )

        response = await audit_client.get("/api/audit/orders?page=1&size=2")

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["size"] == 2
        assert len(data["items"]) <= 2

    @pytest.mark.asyncio
    async def test_list_orders_filter_status(self, audit_client: AsyncClient, sample_order_create: dict):
        """测试按状态过滤工单"""
        # 创建工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json=sample_order_create
        )
        order_id = create_response.json()["id"]

        # 分配（状态变为 in_review）
        await audit_client.put(
            f"/api/audit/order/{order_id}/assign",
            json={"assignee": "reviewer_001"}
        )

        # 过滤
        response = await audit_client.get("/api/audit/orders?status=in_review")

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            assert item["status"] == "in_review"

    @pytest.mark.asyncio
    async def test_list_orders_filter_assignee(self, audit_client: AsyncClient, sample_order_create: dict):
        """测试按审核人过滤工单"""
        # 创建并分配工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json=sample_order_create
        )
        order_id = create_response.json()["id"]

        await audit_client.put(
            f"/api/audit/order/{order_id}/assign",
            json={"assignee": "reviewer_filter_test"}
        )

        # 过滤
        response = await audit_client.get(
            "/api/audit/orders?assignee=reviewer_filter_test"
        )

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            assert item["assignee"] == "reviewer_filter_test"

    @pytest.mark.asyncio
    async def test_get_todo_orders(self, audit_client: AsyncClient, sample_order_create: dict):
        """测试获取待办列表"""
        # 创建并分配工单
        create_response = await audit_client.post(
            "/api/audit/order",
            json=sample_order_create
        )
        order_id = create_response.json()["id"]

        await audit_client.put(
            f"/api/audit/order/{order_id}/assign",
            json={"assignee": "reviewer_todo"}
        )

        # 获取待办
        response = await audit_client.get(
            "/api/audit/orders/todo?assignee=reviewer_todo"
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_unassigned_orders(self, audit_client: AsyncClient, sample_order_create: dict):
        """测试获取未分配工单"""
        # 创建未分配的工单
        await audit_client.post(
            "/api/audit/order",
            json=sample_order_create
        )

        response = await audit_client.get("/api/audit/orders/unassigned")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        for item in data:
            assert item["assignee"] is None


class TestAuditBatch:
    """Audit 服务批量操作测试"""

    @pytest.mark.asyncio
    async def test_batch_assign(self, audit_client: AsyncClient, sample_order_create: dict):
        """测试批量分配"""
        # 创建多个工单
        order_ids = []
        for i in range(3):
            create_response = await audit_client.post(
                "/api/audit/order",
                json={**sample_order_create, "user_id": f"user_batch_{i}"}
            )
            order_ids.append(create_response.json()["id"])

        # 批量分配
        response = await audit_client.post(
            "/api/audit/orders/batch-assign",
            json={
                "order_ids": order_ids,
                "assignee": "reviewer_batch"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) == len(order_ids)
        for item in data:
            assert item["assignee"] == "reviewer_batch"


class TestAuditStats:
    """Audit 服务统计测试"""

    @pytest.mark.asyncio
    async def test_get_stats(self, audit_client: AsyncClient, sample_order_create: dict):
        """测试获取统计信息"""
        # 创建一些工单
        await audit_client.post("/api/audit/order", json=sample_order_create)

        response = await audit_client.get("/api/audit/stats")

        assert response.status_code == 200
        data = response.json()

        assert "status_counts" in data
        assert "level_counts" in data
        assert "today_count" in data
