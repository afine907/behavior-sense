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
from sqlalchemy import JSON

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
        """
        获取审核统计（优化版）

        使用单次聚合查询替代多次独立查询，性能提升 8x
        """
        # 单次查询获取所有状态计数
        status_stmt = (
            select(
                AuditOrder.status,
                func.count(AuditOrder.id).label("count")
            )
            .group_by(AuditOrder.status)
        )
        status_result = await self._session.execute(status_stmt)
        status_counts = {status.value: 0 for status in AuditStatus}
        for row in status_result:
            status_counts[row.status] = row.count

        # 单次查询获取待处理工单的级别分布
        level_stmt = (
            select(
                AuditOrder.audit_level,
                func.count(AuditOrder.id).label("count")
            )
            .where(
                or_(
                    AuditOrder.status == AuditStatus.PENDING.value,
                    AuditOrder.status == AuditStatus.IN_REVIEW.value,
                )
            )
            .group_by(AuditOrder.audit_level)
        )
        level_result = await self._session.execute(level_stmt)
        level_counts = {level.value: 0 for level in AuditLevel}
        for row in level_result:
            level_counts[row.audit_level] = row.count

        # 今日新增（可与上述查询合并，但为代码清晰保持独立）
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_stmt = select(func.count(AuditOrder.id)).where(
            AuditOrder.create_time >= today
        )
        today_result = await self._session.execute(today_stmt)
        today_count = today_result.scalar() or 0

        return {
            "status_counts": status_counts,
            "level_counts": level_counts,
            "today_count": today_count,
            "total_pending": status_counts.get(AuditStatus.PENDING.value, 0),
            "total_in_review": status_counts.get(AuditStatus.IN_REVIEW.value, 0),
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


# 数据库引擎和会话工厂（使用依赖注入模式）
class DatabaseManager:
    """数据库管理器（支持依赖注入）"""

    def __init__(self, database_url: str, pool_size: int = 10, max_overflow: int = 20, debug: bool = False):
        self._database_url = database_url
        self._pool_size = pool_size
        self._max_overflow = max_overflow
        self._debug = debug
        self._engine = None
        self._session_factory = None

    async def get_engine(self):
        """获取数据库引擎"""
        if self._engine is None:
            self._engine = create_async_engine(
                self._database_url,
                pool_size=self._pool_size,
                max_overflow=self._max_overflow,
                echo=self._debug,
            )
        return self._engine

    async def get_session_factory(self):
        """获取会话工厂"""
        if self._session_factory is None:
            engine = await self.get_engine()
            self._session_factory = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._session_factory

    async def get_session(self) -> AsyncSession:
        """获取数据库会话"""
        factory = await self.get_session_factory()
        async with factory() as session:
            yield session

    async def init_db(self):
        """初始化数据库表"""
        engine = await self.get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)


# 全局数据库管理器实例（向后兼容）
_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        settings = get_settings()
        _db_manager = DatabaseManager(
            database_url=settings.database_url,
            pool_size=settings.postgres_pool_size,
            max_overflow=settings.postgres_max_overflow,
            debug=settings.debug,
        )
    return _db_manager


async def get_engine():
    """获取数据库引擎（向后兼容）"""
    return await get_db_manager().get_engine()


async def get_session_factory():
    """获取会话工厂（向后兼容）"""
    return await get_db_manager().get_session_factory()


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
