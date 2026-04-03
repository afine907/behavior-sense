"""
审核仓库层
实现审核工单的数据访问
"""
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel, Field
from sqlmodel.colocations import JSON

from behavior_core.config.settings import get_settings
from behavior_core.utils.logging import get_logger

logger = get_logger(__name__)


class AuditStatus(str, Enum):
    """审核状态枚举"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class AuditLevel(str, Enum):
    """审核级别枚举"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AuditOrder(SQLModel, table=True):
    """审核工单表模型"""
    __tablename__ = "audit_orders"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    rule_id: str = Field(index=True)
    trigger_data: dict[str, Any] = Field(default_factory=dict, sa_type=JSON)
    audit_level: str = Field(default=AuditLevel.MEDIUM.value)
    status: str = Field(default=AuditStatus.PENDING.value, index=True)
    assignee: str | None = Field(default=None, index=True)
    reviewer_note: str | None = Field(default=None)
    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)


class AuditOrderCreate(SQLModel):
    """创建审核工单请求"""
    user_id: str
    rule_id: str
    trigger_data: dict[str, Any] = Field(default_factory=dict)
    audit_level: str = Field(default=AuditLevel.MEDIUM.value)


class AuditOrderUpdate(SQLModel):
    """更新审核工单请求"""
    assignee: str | None = None
    status: str | None = None
    reviewer_note: str | None = None


class AuditRepository:
    """审核仓库"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, order: AuditOrder) -> AuditOrder:
        """创建审核工单"""
        self._session.add(order)
        await self._session.commit()
        await self._session.refresh(order)
        logger.info("Created audit order", order_id=order.id, user_id=order.user_id)
        return order

    async def get_by_id(self, order_id: str) -> AuditOrder | None:
        """根据ID获取工单"""
        statement = select(AuditOrder).where(AuditOrder.id == order_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def update(self, order: AuditOrder) -> AuditOrder:
        """更新工单"""
        order.update_time = datetime.utcnow()
        self._session.add(order)
        await self._session.commit()
        await self._session.refresh(order)
        logger.info("Updated audit order", order_id=order.id, status=order.status)
        return order

    async def list_orders(
        self,
        status: str | None = None,
        assignee: str | None = None,
        user_id: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[AuditOrder], int]:
        """查询工单列表"""
        conditions = []

        if status:
            conditions.append(AuditOrder.status == status)
        if assignee:
            conditions.append(AuditOrder.assignee == assignee)
        if user_id:
            conditions.append(AuditOrder.user_id == user_id)

        # 构建查询条件
        where_clause = and_(*conditions) if conditions else None

        # 查询总数
        count_statement = select(func.count(AuditOrder.id))
        if where_clause is not None:
            count_statement = count_statement.where(where_clause)
        total_result = await self._session.execute(count_statement)
        total = total_result.scalar() or 0

        # 分页查询
        offset = (page - 1) * size
        statement = select(AuditOrder).order_by(AuditOrder.create_time.desc())

        if where_clause is not None:
            statement = statement.where(where_clause)

        statement = statement.offset(offset).limit(size)
        result = await self._session.execute(statement)
        orders = list(result.scalars().all())

        return orders, total

    async def get_todo_list(self, assignee: str) -> list[AuditOrder]:
        """获取待办列表"""
        # 分配给指定人的待处理和审核中的工单
        statement = (
            select(AuditOrder)
            .where(
                and_(
                    AuditOrder.assignee == assignee,
                    or_(
                        AuditOrder.status == AuditStatus.PENDING.value,
                        AuditOrder.status == AuditStatus.IN_REVIEW.value,
                    ),
                )
            )
            .order_by(AuditOrder.audit_level.desc(), AuditOrder.create_time.asc())
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def get_unassigned_pending(self) -> list[AuditOrder]:
        """获取未分配的待处理工单"""
        statement = (
            select(AuditOrder)
            .where(
                and_(
                    AuditOrder.status == AuditStatus.PENDING.value,
                    AuditOrder.assignee.is_(None),
                )
            )
            .order_by(AuditOrder.audit_level.desc(), AuditOrder.create_time.asc())
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def get_stats(self) -> dict[str, Any]:
        """获取审核统计"""
        # 各状态数量统计
        status_counts = {}
        for status in AuditStatus:
            statement = select(func.count(AuditOrder.id)).where(
                AuditOrder.status == status.value
            )
            result = await self._session.execute(statement)
            status_counts[status.value] = result.scalar() or 0

        # 各级别数量统计
        level_counts = {}
        for level in AuditLevel:
            statement = select(func.count(AuditOrder.id)).where(
                and_(
                    AuditOrder.audit_level == level.value,
                    or_(
                        AuditOrder.status == AuditStatus.PENDING.value,
                        AuditOrder.status == AuditStatus.IN_REVIEW.value,
                    ),
                )
            )
            result = await self._session.execute(statement)
            level_counts[level.value] = result.scalar() or 0

        # 今日新增
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        statement = select(func.count(AuditOrder.id)).where(
            AuditOrder.create_time >= today
        )
        result = await self._session.execute(statement)
        today_count = result.scalar() or 0

        return {
            "status_counts": status_counts,
            "level_counts": level_counts,
            "today_count": today_count,
        }

    async def delete(self, order_id: str) -> bool:
        """删除工单"""
        order = await self.get_by_id(order_id)
        if order:
            await self._session.delete(order)
            await self._session.commit()
            logger.info("Deleted audit order", order_id=order_id)
            return True
        return False


# 数据库引擎和会话工厂
_engine = None
_session_factory = None


async def get_engine():
    """获取数据库引擎"""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            pool_size=settings.postgres_pool_size,
            max_overflow=settings.postgres_max_overflow,
            echo=settings.debug,
        )
    return _engine


async def get_session_factory():
    """获取会话工厂"""
    global _session_factory
    if _session_factory is None:
        engine = await get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def init_db():
    """初始化数据库表"""
    engine = await get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Database tables created")


async def get_session() -> AsyncSession:
    """获取数据库会话"""
    factory = await get_session_factory()
    async with factory() as session:
        yield session
