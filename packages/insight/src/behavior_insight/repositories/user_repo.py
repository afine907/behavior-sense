"""
用户仓库
使用 PostgreSQL + SQLAlchemy 异步实现
"""
from datetime import UTC, datetime
from typing import Any

from behavior_core.models import UserProfile, UserStat
from behavior_core.utils.logging import get_logger
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    delete,
    select,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

logger = get_logger(__name__)

Base = declarative_base()


def utcnow_naive() -> datetime:
    """返回无时区信息的 UTC 时间（用于数据库存储）"""
    return datetime.now(UTC).replace(tzinfo=None)


class UserModel(Base):
    """用户数据表模型"""
    __tablename__ = "users"

    user_id = Column(String(64), primary_key=True)
    basic_info = Column(JSON, default=dict)
    behavior_tags = Column(JSON, default=list)
    stat_tags = Column(JSON, default=dict)
    predict_tags = Column(JSON, default=dict)
    risk_level = Column(String(32), default="low")
    create_time = Column(DateTime, default=utcnow_naive)
    update_time = Column(DateTime, default=utcnow_naive, onupdate=utcnow_naive)


class UserStatModel(Base):
    """用户统计数据表模型"""
    __tablename__ = "user_stats"

    user_id = Column(String(64), primary_key=True)
    total_events = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    total_purchases = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)

    events_1d = Column(Integer, default=0)
    events_7d = Column(Integer, default=0)
    events_30d = Column(Integer, default=0)

    purchases_1d = Column(Integer, default=0)
    purchases_7d = Column(Integer, default=0)
    purchases_30d = Column(Integer, default=0)

    amount_1d = Column(Float, default=0.0)
    amount_7d = Column(Float, default=0.0)
    amount_30d = Column(Float, default=0.0)

    last_event_time = Column(DateTime, nullable=True)
    last_purchase_time = Column(DateTime, nullable=True)
    last_login_time = Column(DateTime, nullable=True)

    update_time = Column(DateTime, default=utcnow_naive, onupdate=utcnow_naive)


class UserRepository:
    """用户仓库 - 管理用户画像和统计数据的持久化"""

    def __init__(self, session: AsyncSession):
        """
        初始化用户仓库

        Args:
            session: SQLAlchemy 异步会话
        """
        self._session = session

    async def get_user_profile(self, user_id: str) -> UserProfile | None:
        """
        获取用户画像

        Args:
            user_id: 用户ID

        Returns:
            UserProfile 对象，如果用户不存在则返回 None
        """
        stmt = select(UserModel).where(UserModel.user_id == user_id)
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            return None

        return UserProfile(
            user_id=user.user_id,
            basic_info=user.basic_info or {},
            behavior_tags=user.behavior_tags or [],
            stat_tags=user.stat_tags or {},
            predict_tags=user.predict_tags or {},
            risk_level=user.risk_level or "low",
            create_time=user.create_time,
            update_time=user.update_time,
        )

    async def update_user_profile(
        self,
        user_id: str,
        profile: UserProfile | dict[str, Any],
    ) -> UserProfile:
        """
        更新用户画像 (使用 PostgreSQL UPSERT 避免竞态条件)

        Args:
            user_id: 用户ID
            profile: 画像数据（UserProfile 对象或字典）

        Returns:
            更新后的用户画像
        """
        if isinstance(profile, UserProfile):
            update_data = {
                "basic_info": profile.basic_info,
                "behavior_tags": profile.behavior_tags,
                "stat_tags": profile.stat_tags,
                "predict_tags": profile.predict_tags,
                "risk_level": profile.risk_level,
                "update_time": utcnow_naive(),
            }
        else:
            update_data = {**profile, "update_time": utcnow_naive()}

        # 使用 PostgreSQL INSERT ... ON CONFLICT UPDATE (原子操作，避免竞态条件)
        stmt = pg_insert(UserModel).values(
            user_id=user_id,
            **update_data,
            create_time=utcnow_naive(),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id'],
            set_=update_data,
        )
        await self._session.execute(stmt)
        await self._session.commit()
        logger.info("Upserted user profile", user_id=user_id)

        # 返回更新后的画像
        return await self.get_user_profile(user_id)  # type: ignore

    async def get_user_stat(self, user_id: str) -> UserStat | None:
        """
        获取用户统计

        Args:
            user_id: 用户ID

        Returns:
            UserStat 对象，如果不存在则返回 None
        """
        stmt = select(UserStatModel).where(UserStatModel.user_id == user_id)
        result = await self._session.execute(stmt)
        stat = result.scalar_one_or_none()

        if stat is None:
            return None

        return UserStat(
            user_id=stat.user_id,
            total_events=stat.total_events,
            total_sessions=stat.total_sessions,
            total_purchases=stat.total_purchases,
            total_amount=stat.total_amount,
            events_1d=stat.events_1d,
            events_7d=stat.events_7d,
            events_30d=stat.events_30d,
            purchases_1d=stat.purchases_1d,
            purchases_7d=stat.purchases_7d,
            purchases_30d=stat.purchases_30d,
            amount_1d=stat.amount_1d,
            amount_7d=stat.amount_7d,
            amount_30d=stat.amount_30d,
            last_event_time=stat.last_event_time,
            last_purchase_time=stat.last_purchase_time,
            last_login_time=stat.last_login_time,
            update_time=stat.update_time,
        )

    async def update_user_stat(
        self,
        user_id: str,
        stat: UserStat | dict[str, Any],
    ) -> UserStat:
        """
        更新用户统计 (使用 PostgreSQL UPSERT 避免竞态条件)

        Args:
            user_id: 用户ID
            stat: 统计数据

        Returns:
            更新后的用户统计
        """
        if isinstance(stat, UserStat):
            update_data = {
                "total_events": stat.total_events,
                "total_sessions": stat.total_sessions,
                "total_purchases": stat.total_purchases,
                "total_amount": stat.total_amount,
                "events_1d": stat.events_1d,
                "events_7d": stat.events_7d,
                "events_30d": stat.events_30d,
                "purchases_1d": stat.purchases_1d,
                "purchases_7d": stat.purchases_7d,
                "purchases_30d": stat.purchases_30d,
                "amount_1d": stat.amount_1d,
                "amount_7d": stat.amount_7d,
                "amount_30d": stat.amount_30d,
                "last_event_time": stat.last_event_time,
                "last_purchase_time": stat.last_purchase_time,
                "last_login_time": stat.last_login_time,
                "update_time": utcnow_naive(),
            }
        else:
            update_data = {**stat, "update_time": utcnow_naive()}

        # 使用 PostgreSQL INSERT ... ON CONFLICT UPDATE (原子操作，避免竞态条件)
        stmt = pg_insert(UserStatModel).values(
            user_id=user_id,
            **update_data,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id'],
            set_=update_data,
        )
        await self._session.execute(stmt)
        await self._session.commit()
        logger.info("Upserted user stat", user_id=user_id)

        return await self.get_user_stat(user_id)  # type: ignore

    async def delete_user(self, user_id: str) -> bool:
        """
        删除用户

        Args:
            user_id: 用户ID

        Returns:
            是否成功删除
        """
        # 删除统计记录
        await self._session.execute(
            delete(UserStatModel).where(UserStatModel.user_id == user_id)
        )

        # 删除用户记录
        result = await self._session.execute(
            delete(UserModel).where(UserModel.user_id == user_id)
        )

        await self._session.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info("Deleted user", user_id=user_id)

        return deleted

    async def get_users_by_risk_level(self, risk_level: str) -> list[str]:
        """
        获取指定风险等级的用户列表

        Args:
            risk_level: 风险等级

        Returns:
            用户ID列表
        """
        stmt = select(UserModel.user_id).where(UserModel.risk_level == risk_level)
        result = await self._session.execute(stmt)
        return [row[0] for row in result.fetchall()]

    async def count_users(self) -> int:
        """
        统计用户总数

        Returns:
            用户数量
        """
        from sqlalchemy import func

        stmt = select(func.count(UserModel.user_id))
        result = await self._session.execute(stmt)
        return result.scalar() or 0


async def init_database(database_url: str) -> async_sessionmaker[AsyncSession]:
    """
    初始化数据库连接

    Args:
        database_url: 数据库连接URL

    Returns:
        异步会话工厂
    """
    engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized")

    return async_session
