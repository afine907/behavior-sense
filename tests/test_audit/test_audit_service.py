"""
behavior_audit 模块单元测试
"""
import pytest
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any
from enum import Enum

from behavior_audit.services.audit_service import (
    AuditStateMachine,
    AuditService,
    AuditServiceError,
    InvalidStatusTransitionError,
    OrderNotFoundError,
)


class AuditStatus(str, Enum):
    """审核状态"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class AuditLevel(str, Enum):
    """审核级别"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class AuditOrder:
    """审核工单"""
    id: str
    user_id: str
    rule_id: str
    trigger_data: dict[str, Any] = field(default_factory=dict)
    audit_level: str = "medium"
    status: str = "pending"
    assignee: str | None = None
    reviewer_note: str | None = None
    create_time: datetime = field(default_factory=datetime.utcnow)
    update_time: datetime = field(default_factory=datetime.utcnow)


class MockAuditRepository:
    """模拟审核仓库"""

    def __init__(self):
        self.orders: dict[str, AuditOrder] = {}
        self._counter = 0

    async def create(self, order: AuditOrder) -> AuditOrder:
        self.orders[order.id] = order
        return order

    async def get_by_id(self, order_id: str) -> AuditOrder | None:
        return self.orders.get(order_id)

    async def update(self, order: AuditOrder) -> AuditOrder:
        order.update_time = datetime.utcnow()
        self.orders[order.id] = order
        return order

    async def list_orders(
        self,
        status: str | None = None,
        assignee: str | None = None,
        user_id: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[AuditOrder], int]:
        orders = list(self.orders.values())

        if status:
            orders = [o for o in orders if o.status == status]
        if assignee:
            orders = [o for o in orders if o.assignee == assignee]
        if user_id:
            orders = [o for o in orders if o.user_id == user_id]

        total = len(orders)
        start = (page - 1) * size
        end = start + size
        return orders[start:end], total

    async def get_todo_list(self, assignee: str) -> list[AuditOrder]:
        return [
            o for o in self.orders.values()
            if o.assignee == assignee and o.status == "in_review"
        ]

    async def get_unassigned_pending(self) -> list[AuditOrder]:
        return [
            o for o in self.orders.values()
            if o.assignee is None and o.status == "pending"
        ]

    async def get_stats(self) -> dict[str, Any]:
        stats = {
            "total": len(self.orders),
            "pending": 0,
            "in_review": 0,
            "approved": 0,
            "rejected": 0,
            "closed": 0,
        }
        for order in self.orders.values():
            stats[order.status] = stats.get(order.status, 0) + 1
        return stats


class TestAuditStateMachine:
    """审核状态机测试"""

    def test_valid_transitions_from_pending(self):
        """测试从 PENDING 状态的有效转换"""
        assert AuditStateMachine.can_transition(AuditStatus.PENDING, AuditStatus.IN_REVIEW)
        assert AuditStateMachine.can_transition(AuditStatus.PENDING, AuditStatus.CLOSED)
        assert not AuditStateMachine.can_transition(AuditStatus.PENDING, AuditStatus.APPROVED)

    def test_valid_transitions_from_in_review(self):
        """测试从 IN_REVIEW 状态的有效转换"""
        assert AuditStateMachine.can_transition(AuditStatus.IN_REVIEW, AuditStatus.APPROVED)
        assert AuditStateMachine.can_transition(AuditStatus.IN_REVIEW, AuditStatus.REJECTED)
        assert AuditStateMachine.can_transition(AuditStatus.IN_REVIEW, AuditStatus.PENDING)

    def test_valid_transitions_from_approved(self):
        """测试从 APPROVED 状态的有效转换"""
        assert AuditStateMachine.can_transition(AuditStatus.APPROVED, AuditStatus.CLOSED)
        assert not AuditStateMachine.can_transition(AuditStatus.APPROVED, AuditStatus.REJECTED)

    def test_valid_transitions_from_rejected(self):
        """测试从 REJECTED 状态的有效转换"""
        assert AuditStateMachine.can_transition(AuditStatus.REJECTED, AuditStatus.CLOSED)
        assert AuditStateMachine.can_transition(AuditStatus.REJECTED, AuditStatus.IN_REVIEW)

    def test_no_transitions_from_closed(self):
        """测试 CLOSED 状态不允许转换"""
        assert not AuditStateMachine.can_transition(AuditStatus.CLOSED, AuditStatus.PENDING)
        assert not AuditStateMachine.can_transition(AuditStatus.CLOSED, AuditStatus.IN_REVIEW)

    def test_get_next_statuses(self):
        """测试获取下一状态列表"""
        next_statuses = AuditStateMachine.get_next_statuses(AuditStatus.PENDING)
        assert AuditStatus.IN_REVIEW in next_statuses
        assert AuditStatus.CLOSED in next_statuses


class TestAuditService:
    """审核服务测试"""

    @pytest.fixture
    def mock_repo(self):
        return MockAuditRepository()

    @pytest.fixture
    def audit_service(self, mock_repo):
        return AuditService(mock_repo)

    @pytest.mark.asyncio
    async def test_create_order(self, audit_service):
        """测试创建工单"""
        order = await audit_service.create_order(
            user_id="user_001",
            rule_id="rule_001",
            trigger_data={"amount": 10000},
        )

        assert order.id is not None
        assert order.user_id == "user_001"
        assert order.status == "pending"

    @pytest.mark.asyncio
    async def test_create_order_with_level(self, audit_service):
        """测试创建带级别的工单"""
        order = await audit_service.create_order(
            user_id="user_001",
            rule_id="rule_001",
            trigger_data={},
            level="HIGH",
        )

        assert order.audit_level == "HIGH"

    @pytest.mark.asyncio
    async def test_get_order(self, audit_service):
        """测试获取工单"""
        created = await audit_service.create_order(
            user_id="user_001",
            rule_id="rule_001",
            trigger_data={},
        )

        order = await audit_service.get_order(created.id)
        assert order.id == created.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_order(self, audit_service):
        """测试获取不存在的工单"""
        with pytest.raises(OrderNotFoundError):
            await audit_service.get_order("nonexistent_id")

    @pytest.mark.asyncio
    async def test_assign_order(self, audit_service):
        """测试分配工单"""
        created = await audit_service.create_order(
            user_id="user_001",
            rule_id="rule_001",
            trigger_data={},
        )

        order = await audit_service.assign_order(created.id, "reviewer_001")

        assert order.assignee == "reviewer_001"
        assert order.status == "in_review"

    @pytest.mark.asyncio
    async def test_assign_non_pending_order(self, audit_service):
        """测试分配非待处理状态的工单"""
        created = await audit_service.create_order(
            user_id="user_001",
            rule_id="rule_001",
            trigger_data={},
        )

        # 先分配一次
        await audit_service.assign_order(created.id, "reviewer_001")

        # 再次分配应该失败
        with pytest.raises(InvalidStatusTransitionError):
            await audit_service.assign_order(created.id, "reviewer_002")

    @pytest.mark.asyncio
    async def test_submit_review_approve(self, audit_service):
        """测试提交审核 - 通过"""
        created = await audit_service.create_order(
            user_id="user_001",
            rule_id="rule_001",
            trigger_data={},
        )
        await audit_service.assign_order(created.id, "reviewer_001")

        order = await audit_service.submit_review(
            order_id=created.id,
            status="approved",
            note="审核通过",
        )

        assert order.status == "approved"
        assert order.reviewer_note == "审核通过"

    @pytest.mark.asyncio
    async def test_submit_review_reject(self, audit_service):
        """测试提交审核 - 驳回"""
        created = await audit_service.create_order(
            user_id="user_001",
            rule_id="rule_001",
            trigger_data={},
        )
        await audit_service.assign_order(created.id, "reviewer_001")

        order = await audit_service.submit_review(
            order_id=created.id,
            status="rejected",
            note="风险过高",
        )

        assert order.status == "rejected"

    @pytest.mark.asyncio
    async def test_invalid_status_transition(self, audit_service):
        """测试无效的状态转换"""
        created = await audit_service.create_order(
            user_id="user_001",
            rule_id="rule_001",
            trigger_data={},
        )

        # 直接从 pending 跳到 approved 是不允许的
        with pytest.raises(InvalidStatusTransitionError):
            await audit_service.submit_review(
                order_id=created.id,
                status="approved",
            )

    @pytest.mark.asyncio
    async def test_list_orders(self, audit_service):
        """测试查询工单列表"""
        await audit_service.create_order("user_001", "rule_001", {})
        await audit_service.create_order("user_002", "rule_001", {})
        await audit_service.create_order("user_003", "rule_002", {})

        orders, total = await audit_service.list_orders(page=1, size=10)

        assert total == 3
        assert len(orders) == 3

    @pytest.mark.asyncio
    async def test_list_orders_by_status(self, audit_service):
        """测试按状态查询工单"""
        created = await audit_service.create_order("user_001", "rule_001", {})
        await audit_service.assign_order(created.id, "reviewer_001")

        orders, total = await audit_service.list_orders(status="in_review")

        assert total == 1
        assert orders[0].status == "in_review"

    @pytest.mark.asyncio
    async def test_get_todo_list(self, audit_service):
        """测试获取待办列表"""
        created = await audit_service.create_order("user_001", "rule_001", {})
        await audit_service.assign_order(created.id, "reviewer_001")

        todos = await audit_service.get_todo_list("reviewer_001")

        assert len(todos) == 1
        assert todos[0].assignee == "reviewer_001"

    @pytest.mark.asyncio
    async def test_get_unassigned_pending(self, audit_service):
        """测试获取未分配的待处理工单"""
        await audit_service.create_order("user_001", "rule_001", {})
        created = await audit_service.create_order("user_002", "rule_001", {})
        await audit_service.assign_order(created.id, "reviewer_001")

        unassigned = await audit_service.get_unassigned_pending()

        assert len(unassigned) == 1
        assert unassigned[0].assignee is None

    @pytest.mark.asyncio
    async def test_close_order(self, audit_service):
        """测试关闭工单"""
        created = await audit_service.create_order("user_001", "rule_001", {})

        order = await audit_service.close_order(created.id, note="用户正常")

        assert order.status == "closed"

    @pytest.mark.asyncio
    async def test_reopen_order(self, audit_service):
        """测试重新打开工单"""
        created = await audit_service.create_order("user_001", "rule_001", {})
        await audit_service.assign_order(created.id, "reviewer_001")
        await audit_service.submit_review(created.id, "rejected")

        order = await audit_service.reopen_order(created.id, "reviewer_002")

        assert order.status == "in_review"
        assert order.assignee == "reviewer_002"

    @pytest.mark.asyncio
    async def test_batch_assign(self, audit_service):
        """测试批量分配"""
        order1 = await audit_service.create_order("user_001", "rule_001", {})
        order2 = await audit_service.create_order("user_002", "rule_001", {})

        assigned = await audit_service.batch_assign(
            [order1.id, order2.id],
            "reviewer_001"
        )

        assert len(assigned) == 2

    @pytest.mark.asyncio
    async def test_get_stats(self, audit_service):
        """测试获取统计"""
        await audit_service.create_order("user_001", "rule_001", {})
        created = await audit_service.create_order("user_002", "rule_001", {})
        await audit_service.assign_order(created.id, "reviewer_001")

        stats = await audit_service.get_stats()

        assert stats["total"] == 2
        assert stats["pending"] == 1
        assert stats["in_review"] == 1
