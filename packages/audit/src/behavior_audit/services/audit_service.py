"""
审核服务层
实现审核工单的业务逻辑
"""
from typing import Any
from uuid import uuid4

from behavior_core.utils.logging import get_logger

from behavior_audit.repositories.audit_repo import (
    AuditLevel,
    AuditOrder,
    AuditRepository,
    AuditStatus,
)

logger = get_logger(__name__)


class AuditStateMachine:
    """审核状态机"""

    # 状态转换规则
    TRANSITIONS = {
        AuditStatus.PENDING: [AuditStatus.IN_REVIEW, AuditStatus.CLOSED],
        AuditStatus.IN_REVIEW: [AuditStatus.APPROVED, AuditStatus.REJECTED, AuditStatus.PENDING],
        AuditStatus.APPROVED: [AuditStatus.CLOSED],
        AuditStatus.REJECTED: [AuditStatus.CLOSED, AuditStatus.IN_REVIEW],
        AuditStatus.CLOSED: [],
    }

    @classmethod
    def can_transition(cls, from_status: AuditStatus, to_status: AuditStatus) -> bool:
        """检查状态转换是否合法"""
        allowed = cls.TRANSITIONS.get(from_status, [])
        return to_status in allowed

    @classmethod
    def get_next_statuses(cls, current_status: AuditStatus) -> list[AuditStatus]:
        """获取可转换的下一状态列表"""
        return cls.TRANSITIONS.get(current_status, [])


class AuditServiceError(Exception):
    """审核服务异常"""
    pass


class InvalidStatusTransitionError(AuditServiceError):
    """无效的状态转换"""
    pass


class OrderNotFoundError(AuditServiceError):
    """工单不存在"""
    pass


class AuditService:
    """审核服务"""

    def __init__(self, repository: AuditRepository):
        self._repo = repository

    async def create_order(
        self,
        user_id: str,
        rule_id: str,
        trigger_data: dict[str, Any],
        level: str = AuditLevel.MEDIUM.value,
    ) -> AuditOrder:
        """
        创建审核工单

        Args:
            user_id: 用户ID
            rule_id: 触发的规则ID
            trigger_data: 触发数据
            level: 审核级别 (HIGH/MEDIUM/LOW)

        Returns:
            创建的审核工单
        """
        # 验证审核级别
        if level not in [lvl.value for lvl in AuditLevel]:
            level = AuditLevel.MEDIUM.value

        order = AuditOrder(
            id=str(uuid4()),
            user_id=user_id,
            rule_id=rule_id,
            trigger_data=trigger_data,
            audit_level=level,
            status=AuditStatus.PENDING.value,
        )

        order = await self._repo.create(order)
        logger.info(
            "Created audit order",
            order_id=order.id,
            user_id=user_id,
            rule_id=rule_id,
            level=level,
        )
        return order

    async def get_order(self, order_id: str) -> AuditOrder:
        """
        获取工单详情

        Args:
            order_id: 工单ID

        Returns:
            审核工单详情

        Raises:
            OrderNotFoundError: 工单不存在
        """
        order = await self._repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order {order_id} not found")
        return order

    async def list_orders(
        self,
        status: str | None = None,
        assignee: str | None = None,
        user_id: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[AuditOrder], int]:
        """
        查询工单列表

        Args:
            status: 状态过滤
            assignee: 审核人过滤
            user_id: 用户ID过滤
            page: 页码
            size: 每页数量

        Returns:
            (工单列表, 总数)
        """
        return await self._repo.list_orders(
            status=status,
            assignee=assignee,
            user_id=user_id,
            page=page,
            size=size,
        )

    async def assign_order(self, order_id: str, assignee: str) -> AuditOrder:
        """
        分配审核人

        Args:
            order_id: 工单ID
            assignee: 审核人ID

        Returns:
            更新后的工单

        Raises:
            OrderNotFoundError: 工单不存在
            InvalidStatusTransitionError: 状态不允许分配
        """
        order = await self.get_order(order_id)
        current_status = AuditStatus(order.status)

        # 只有 PENDING 状态可以分配
        if current_status != AuditStatus.PENDING:
            raise InvalidStatusTransitionError(
                f"Cannot assign order in status {current_status.value}"
            )

        order.assignee = assignee
        order.status = AuditStatus.IN_REVIEW.value
        order = await self._repo.update(order)

        logger.info(
            "Assigned audit order",
            order_id=order_id,
            assignee=assignee,
        )
        return order

    async def submit_review(
        self,
        order_id: str,
        status: str,
        note: str | None = None,
        reviewer: str | None = None,
    ) -> AuditOrder:
        """
        提交审核结果

        Args:
            order_id: 工单ID
            status: 新状态 (approved/rejected/closed)
            note: 审核备注
            reviewer: 审核人ID

        Returns:
            更新后的工单

        Raises:
            OrderNotFoundError: 工单不存在
            InvalidStatusTransitionError: 状态转换不合法
        """
        order = await self.get_order(order_id)
        current_status = AuditStatus(order.status)

        # 验证新状态
        try:
            new_status = AuditStatus(status)
        except ValueError:
            raise InvalidStatusTransitionError(f"Invalid status: {status}")

        # 检查状态转换是否合法
        if not AuditStateMachine.can_transition(current_status, new_status):
            raise InvalidStatusTransitionError(
                f"Cannot transition from {current_status.value} to {new_status.value}"
            )

        order.status = new_status.value
        if note:
            order.reviewer_note = note
        if reviewer:
            order.assignee = reviewer

        order = await self._repo.update(order)

        logger.info(
            "Submitted review",
            order_id=order_id,
            status=status,
            reviewer=reviewer,
        )
        return order

    async def get_todo_list(self, assignee: str) -> list[AuditOrder]:
        """
        获取待办列表

        Args:
            assignee: 审核人ID

        Returns:
            待处理工单列表
        """
        return await self._repo.get_todo_list(assignee)

    async def get_unassigned_pending(self) -> list[AuditOrder]:
        """
        获取未分配的待处理工单

        Returns:
            未分配的待处理工单列表
        """
        return await self._repo.get_unassigned_pending()

    async def close_order(self, order_id: str, note: str | None = None) -> AuditOrder:
        """
        关闭工单

        Args:
            order_id: 工单ID
            note: 关闭原因

        Returns:
            更新后的工单
        """
        return await self.submit_review(
            order_id=order_id,
            status=AuditStatus.CLOSED.value,
            note=note,
        )

    async def reopen_order(self, order_id: str, assignee: str | None = None) -> AuditOrder:
        """
        重新打开工单（从驳回状态）

        Args:
            order_id: 工单ID
            assignee: 新的审核人

        Returns:
            更新后的工单
        """
        order = await self.get_order(order_id)
        current_status = AuditStatus(order.status)

        if current_status == AuditStatus.REJECTED:
            order.status = AuditStatus.IN_REVIEW.value
            if assignee:
                order.assignee = assignee
            order = await self._repo.update(order)
            logger.info("Reopened audit order", order_id=order_id)

        return order

    async def get_stats(self) -> dict[str, Any]:
        """
        获取审核统计

        Returns:
            统计数据
        """
        return await self._repo.get_stats()

    async def batch_assign(self, order_ids: list[str], assignee: str) -> list[AuditOrder]:
        """
        批量分配审核人

        Args:
            order_ids: 工单ID列表
            assignee: 审核人ID

        Returns:
            成功分配的工单列表
        """
        assigned = []
        for order_id in order_ids:
            try:
                order = await self.assign_order(order_id, assignee)
                assigned.append(order)
            except AuditServiceError as e:
                logger.warning(
                    "Failed to assign order",
                    order_id=order_id,
                    error=str(e),
                )
        return assigned
