"""
Agent仓库
使用 PostgreSQL + SQLAlchemy 异步实现
"""
from datetime import UTC, datetime
from typing import Any

from behavior_core.utils.logging import get_logger
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from behavior_insight.models.agent_db import AgentProfileDB, AgentStatDB, AgentTagDB

logger = get_logger(__name__)


def utcnow_naive() -> datetime:
    """返回无时区信息的 UTC 时间（用于数据库存储）"""
    return datetime.now(UTC).replace(tzinfo=None)


class AgentRepository:
    """Agent仓库 - 管理Agent画像、统计数据和标签的持久化"""

    def __init__(self, session: AsyncSession):
        """
        初始化Agent仓库

        Args:
            session: SQLAlchemy 异步会话
        """
        self._session = session

    # ============================================================
    # Agent Profile CRUD
    # ============================================================

    async def list_agents(
        self,
        agent_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        列出所有Agent（支持过滤和分页）

        Args:
            agent_type: 按Agent类型过滤
            status: 按状态过滤
            page: 页码（从1开始）
            page_size: 每页数量

        Returns:
            (agent列表, 总数) 元组
        """
        # 构建查询
        stmt = select(AgentProfileDB)
        count_stmt = select(func.count(AgentProfileDB.agent_id))

        if agent_type:
            stmt = stmt.where(AgentProfileDB.agent_type == agent_type)
            count_stmt = count_stmt.where(AgentProfileDB.agent_type == agent_type)
        if status:
            stmt = stmt.where(AgentProfileDB.status == status)
            count_stmt = count_stmt.where(AgentProfileDB.status == status)

        # 获取总数
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self._session.execute(stmt)
        agents = result.scalars().all()

        return [self._profile_to_dict(a) for a in agents], total

    async def get_agent_profile(self, agent_id: str) -> dict[str, Any] | None:
        """
        获取Agent画像

        Args:
            agent_id: Agent ID

        Returns:
            Agent画像字典，如果不存在则返回 None
        """
        stmt = select(AgentProfileDB).where(AgentProfileDB.agent_id == agent_id)
        result = await self._session.execute(stmt)
        agent = result.scalar_one_or_none()

        if agent is None:
            return None

        return self._profile_to_dict(agent)

    async def upsert_agent_profile(
        self,
        agent_id: str,
        profile_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        更新或创建Agent画像（使用 PostgreSQL UPSERT 避免竞态条件）

        Args:
            agent_id: Agent ID
            profile_data: 画像数据

        Returns:
            更新后的Agent画像字典
        """
        now = utcnow_naive()
        update_data = {**profile_data, "update_time": now}

        stmt = pg_insert(AgentProfileDB).values(
            agent_id=agent_id,
            **update_data,
            create_time=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["agent_id"],
            set_=update_data,
        )
        await self._session.execute(stmt)
        await self._session.commit()
        logger.info("Upserted agent profile", agent_id=agent_id)

        return await self.get_agent_profile(agent_id)  # type: ignore

    async def delete_agent(self, agent_id: str) -> bool:
        """
        删除Agent及所有关联数据

        Args:
            agent_id: Agent ID

        Returns:
            是否成功删除
        """
        # 删除标签
        await self._session.execute(
            delete(AgentTagDB).where(AgentTagDB.agent_id == agent_id)
        )

        # 删除统计
        await self._session.execute(
            delete(AgentStatDB).where(AgentStatDB.agent_id == agent_id)
        )

        # 删除画像
        result = await self._session.execute(
            delete(AgentProfileDB).where(AgentProfileDB.agent_id == agent_id)
        )

        await self._session.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info("Deleted agent", agent_id=agent_id)

        return deleted

    # ============================================================
    # Agent Stats CRUD
    # ============================================================

    async def get_agent_stats(self, agent_id: str) -> dict[str, Any] | None:
        """
        获取Agent统计数据

        Args:
            agent_id: Agent ID

        Returns:
            Agent统计字典，如果不存在则返回 None
        """
        stmt = select(AgentStatDB).where(AgentStatDB.agent_id == agent_id)
        result = await self._session.execute(stmt)
        stat = result.scalar_one_or_none()

        if stat is None:
            return None

        return self._stat_to_dict(stat)

    async def upsert_agent_stats(
        self,
        agent_id: str,
        stats_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        更新或创建Agent统计数据

        Args:
            agent_id: Agent ID
            stats_data: 统计数据

        Returns:
            更新后的Agent统计字典
        """
        now = utcnow_naive()
        update_data = {**stats_data, "update_time": now}

        stmt = pg_insert(AgentStatDB).values(
            agent_id=agent_id,
            **update_data,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["agent_id"],
            set_=update_data,
        )
        await self._session.execute(stmt)
        await self._session.commit()
        logger.info("Upserted agent stats", agent_id=agent_id)

        return await self.get_agent_stats(agent_id)  # type: ignore

    # ============================================================
    # Agent Tags CRUD
    # ============================================================

    async def get_agent_tags(self, agent_id: str) -> dict[str, dict[str, Any]]:
        """
        获取Agent的所有标签

        Args:
            agent_id: Agent ID

        Returns:
            标签字典 {tag_name: {value, source, confidence, timestamp}}
        """
        stmt = select(AgentTagDB).where(AgentTagDB.agent_id == agent_id)
        result = await self._session.execute(stmt)
        tags = result.scalars().all()

        return {
            tag.tag_name: {
                "value": tag.tag_value,
                "source": tag.source,
                "confidence": tag.confidence,
                "timestamp": tag.update_time.isoformat() if tag.update_time else None,
            }
            for tag in tags
        }

    async def upsert_agent_tag(
        self,
        agent_id: str,
        tag_name: str,
        tag_value: str,
        source: str = "AUTO",
        confidence: float = 1.0,
    ) -> None:
        """
        更新或创建Agent标签

        Args:
            agent_id: Agent ID
            tag_name: 标签名称
            tag_value: 标签值
            source: 标签来源
            confidence: 置信度
        """
        now = utcnow_naive()
        stmt = pg_insert(AgentTagDB).values(
            agent_id=agent_id,
            tag_name=tag_name,
            tag_value=tag_value,
            source=source,
            confidence=confidence,
            create_time=now,
            update_time=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["agent_id", "tag_name"],
            set_={
                "tag_value": tag_value,
                "source": source,
                "confidence": confidence,
                "update_time": now,
            },
        )
        await self._session.execute(stmt)
        await self._session.commit()
        logger.info("Upserted agent tag", agent_id=agent_id, tag_name=tag_name)

    async def delete_agent_tag(self, agent_id: str, tag_name: str) -> bool:
        """
        删除Agent标签

        Args:
            agent_id: Agent ID
            tag_name: 标签名称

        Returns:
            是否成功删除
        """
        result = await self._session.execute(
            delete(AgentTagDB).where(
                AgentTagDB.agent_id == agent_id,
                AgentTagDB.tag_name == tag_name,
            )
        )
        await self._session.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info("Deleted agent tag", agent_id=agent_id, tag_name=tag_name)

        return deleted

    async def get_agents_by_tag(
        self,
        tag_name: str,
        tag_value: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        按标签查找Agent

        Args:
            tag_name: 标签名称
            tag_value: 标签值（可选）

        Returns:
            匹配的Agent列表
        """
        stmt = select(AgentTagDB).where(AgentTagDB.tag_name == tag_name)
        if tag_value is not None:
            stmt = stmt.where(AgentTagDB.tag_value == tag_value)

        result = await self._session.execute(stmt)
        tags = result.scalars().all()

        return [
            {
                "agent_id": tag.agent_id,
                "tag": {
                    "value": tag.tag_value,
                    "source": tag.source,
                    "confidence": tag.confidence,
                    "timestamp": tag.update_time.isoformat() if tag.update_time else None,
                },
            }
            for tag in tags
        ]

    # ============================================================
    # Agent Overview & Comparison
    # ============================================================

    async def get_agents_overview(self) -> dict[str, Any]:
        """
        获取所有Agent的概览统计

        Returns:
            概览统计数据
        """
        # 总数和活跃数
        total_stmt = select(func.count(AgentProfileDB.agent_id))
        total_result = await self._session.execute(total_stmt)
        total_agents = total_result.scalar() or 0

        active_stmt = select(func.count(AgentProfileDB.agent_id)).where(
            AgentProfileDB.status == "active"
        )
        active_result = await self._session.execute(active_stmt)
        active_agents = active_result.scalar() or 0

        # 统计汇总
        stats_stmt = select(
            func.coalesce(func.sum(AgentStatDB.total_cost_usd), 0.0),
            func.coalesce(func.sum(AgentStatDB.total_events), 0),
            func.coalesce(func.sum(AgentStatDB.total_tokens), 0),
            func.coalesce(func.avg(AgentStatDB.success_rate), 0.0),
        )
        stats_result = await self._session.execute(stats_stmt)
        row = stats_result.one()

        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "total_cost_usd": round(float(row[0]), 2),
            "total_events": int(row[1]),
            "total_tokens": int(row[2]),
            "avg_success_rate": round(float(row[3]), 3),
        }

    async def get_cost_summary(self) -> dict[str, Any]:
        """
        获取所有Agent的成本汇总

        Returns:
            成本汇总数据
        """
        # 按Agent统计
        agent_stmt = select(
            AgentStatDB.agent_id,
            AgentStatDB.total_cost_usd,
        )
        result = await self._session.execute(agent_stmt)
        rows = result.all()

        by_agent: dict[str, float] = {}
        total_cost = 0.0

        for agent_id, cost in rows:
            cost = cost or 0.0
            by_agent[agent_id] = cost
            total_cost += cost

        return {
            "total_cost_usd": round(total_cost, 2),
            "by_agent": by_agent,
            "by_model": {},
        }

    async def get_agent_comparison(
        self,
        agent_ids: list[str],
        metrics: list[str],
    ) -> dict[str, Any]:
        """
        对比多个Agent的指标

        Args:
            agent_ids: Agent ID列表
            metrics: 要对比的指标列表

        Returns:
            对比结果
        """
        # 获取所有Agent的统计数据
        stmt = select(AgentStatDB).where(AgentStatDB.agent_id.in_(agent_ids))
        result = await self._session.execute(stmt)
        stats = {s.agent_id: self._stat_to_dict(s) for s in result.scalars().all()}

        metrics_data: dict[str, dict[str, float]] = {}
        rankings: dict[str, list[str]] = {}

        for metric in metrics:
            metric_values: dict[str, float] = {}
            for agent_id in agent_ids:
                agent_stats = stats.get(agent_id, {})
                metric_values[agent_id] = agent_stats.get(metric, 0.0)

            metrics_data[metric] = metric_values

            # 排序（cost/latency 越低越好，success_rate 越高越好）
            reverse = metric in ("success_rate",)
            sorted_agents = sorted(
                metric_values.keys(),
                key=lambda a: metric_values[a],
                reverse=reverse,
            )
            rankings[metric] = sorted_agents

        # 生成洞察
        insights: list[str] = []
        if "success_rate" in rankings and len(agent_ids) > 1:
            best = rankings["success_rate"][0]
            worst = rankings["success_rate"][-1]
            insights.append(f"Best performing agent: {best}")
            if (
                metrics_data["success_rate"][best]
                - metrics_data["success_rate"][worst]
                > 0.2
            ):
                insights.append(
                    f"Significant performance gap between {best} and {worst}"
                )

        return {
            "agents": agent_ids,
            "metrics": metrics_data,
            "rankings": rankings,
            "insights": insights,
        }

    # ============================================================
    # Helper Methods
    # ============================================================

    @staticmethod
    def _profile_to_dict(agent: AgentProfileDB) -> dict[str, Any]:
        """将AgentProfileDB转换为字典"""
        return {
            "agent_id": agent.agent_id,
            "agent_name": agent.agent_name,
            "agent_type": agent.agent_type,
            "model_name": agent.model_name,
            "framework": agent.framework,
            "owner": agent.owner,
            "status": agent.status or "active",
            "safety_rating": agent.safety_rating or "standard",
            "cost_tier": agent.cost_tier or "standard",
            "capabilities": agent.capabilities or [],
            "supported_tools": agent.supported_tools or [],
            "capability_scores": {},
            "risk_score": agent.risk_score or 0.0,
            "create_time": agent.create_time,
            "update_time": agent.update_time,
            "last_active": agent.last_active,
        }

    @staticmethod
    def _stat_to_dict(stat: AgentStatDB) -> dict[str, Any]:
        """将AgentStatDB转换为字典"""
        return {
            "agent_id": stat.agent_id,
            "total_events": stat.total_events or 0,
            "total_sessions": stat.total_sessions or 0,
            "total_tasks": stat.total_tasks or 0,
            "total_tool_calls": stat.total_tool_calls or 0,
            "total_llm_calls": stat.total_llm_calls or 0,
            "total_tokens": stat.total_tokens or 0,
            "total_cost_usd": stat.total_cost_usd or 0.0,
            "avg_latency_ms": stat.avg_latency_ms or 0.0,
            "success_rate": stat.success_rate or 0.0,
            "error_rate": stat.error_rate or 0.0,
            "p95_latency_ms": stat.p95_latency_ms or 0.0,
            "p99_latency_ms": 0.0,
            "timeout_rate": stat.timeout_rate or 0.0,
            "cost_by_model": {},
            "cost_by_tool": {},
            "events_1d": stat.events_1d or 0,
            "events_7d": stat.events_7d or 0,
            "tokens_1d": stat.tokens_1d or 0,
            "tokens_7d": stat.tokens_7d or 0,
            "cost_1d": stat.cost_1d or 0.0,
            "cost_7d": stat.cost_7d or 0.0,
            "cost_30d": stat.cost_30d or 0.0,
            "update_time": stat.update_time,
        }
