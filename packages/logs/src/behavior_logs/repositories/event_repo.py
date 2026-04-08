"""
事件日志仓库 - ClickHouse 实现
"""
from datetime import datetime
from typing import Any

import clickhouse_connect
import orjson
from behavior_core.config.settings import get_settings
from behavior_core.models.event import UserBehavior
from behavior_core.utils.logging import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)


# ============== 查询模型 ==============


class EventLogQuery(BaseModel):
    """事件查询参数"""

    user_id: str | None = None
    event_type: str | None = None
    session_id: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    page_url: str | None = None
    ip_address: str | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=50, ge=1, le=200)
    sort_order: str = Field(default="desc")  # asc or desc


class EventLogItem(BaseModel):
    """事件日志项"""

    event_id: str
    user_id: str
    event_type: str
    timestamp: datetime
    session_id: str | None = None
    page_url: str | None = None
    referrer: str | None = None
    user_agent: str | None = None
    ip_address: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    ingested_at: datetime | None = None


class EventLogListResponse(BaseModel):
    """事件列表响应"""

    items: list[EventLogItem]
    total: int
    page: int
    size: int


class EventStats(BaseModel):
    """事件统计"""

    total_events: int
    unique_users: int
    unique_sessions: int
    event_type_counts: dict[str, int] = Field(default_factory=dict)


# ============== Repository ==============


class EventLogRepository:
    """ClickHouse 事件日志仓库"""

    def __init__(self, client: clickhouse_connect.driver.Client | None = None):
        settings = get_settings()
        self._client = client or clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password.get_secret_value(),
            database=settings.clickhouse_database,
        )

    def _get_client(self) -> clickhouse_connect.driver.Client:
        """获取客户端实例"""
        return self._client

    # ----- 写入操作 -----

    async def insert_event(self, event: UserBehavior) -> None:
        """插入单个事件"""
        await self.insert_events([event])

    async def insert_events(self, events: list[UserBehavior]) -> None:
        """批量插入事件"""
        if not events:
            return

        rows = []
        for event in events:
            event_type_value = (
                event.event_type.value
                if hasattr(event.event_type, "value")
                else str(event.event_type)
            )
            rows.append(
                [
                    event.event_id,
                    event.timestamp.date(),
                    event.user_id,
                    event_type_value,
                    event.timestamp,
                    event.session_id or "",
                    event.page_url or "",
                    event.referrer or "",
                    event.user_agent or "",
                    event.ip_address or "",
                    orjson.dumps(event.properties).decode(),
                ]
            )

        self._client.insert(
            "event_logs",
            rows,
            column_names=[
                "event_id",
                "event_date",
                "user_id",
                "event_type",
                "timestamp",
                "session_id",
                "page_url",
                "referrer",
                "user_agent",
                "ip_address",
                "properties",
            ],
        )
        logger.info("events_inserted_to_clickhouse", count=len(events))

    # ----- 查询操作 -----

    async def query_events(
        self, query: EventLogQuery
    ) -> tuple[list[EventLogItem], int]:
        """查询事件日志"""
        conditions = []
        params: dict[str, Any] = {}

        # 构建条件
        if query.user_id:
            conditions.append("user_id = {user_id: String}")
            params["user_id"] = query.user_id

        if query.event_type:
            conditions.append("event_type = {event_type: String}")
            params["event_type"] = query.event_type

        if query.session_id:
            conditions.append("session_id = {session_id: String}")
            params["session_id"] = query.session_id

        if query.start_time:
            conditions.append("timestamp >= {start_time: DateTime64(3)}")
            params["start_time"] = query.start_time

        if query.end_time:
            conditions.append("timestamp <= {end_time: DateTime64(3)}")
            params["end_time"] = query.end_time

        if query.page_url:
            conditions.append("page_url LIKE {page_url: String}")
            params["page_url"] = f"%{query.page_url}%"

        if query.ip_address:
            conditions.append("ip_address = {ip_address: String}")
            params["ip_address"] = query.ip_address

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        # Use whitelist for ORDER BY direction to prevent SQL injection
        order_directions = {"asc": "ASC", "desc": "DESC"}
        order_dir = order_directions.get(query.sort_order.lower(), "DESC")
        offset = (query.page - 1) * query.size

        # 查询总数
        count_sql = f"SELECT count() as total FROM event_logs WHERE {where_clause}"
        count_result = self._client.query(count_sql, params)
        total = count_result.first_item["total"]

        # 分页查询
        data_sql = f"""
            SELECT
                event_id, user_id, event_type, timestamp,
                session_id, page_url, referrer, user_agent, ip_address,
                properties, ingested_at
            FROM event_logs
            WHERE {where_clause}
            ORDER BY timestamp {order_dir}, event_id {order_dir}
            LIMIT {query.size} OFFSET {offset}
        """
        result = self._client.query(data_sql, params)

        items = []
        for row in result.result_rows:
            items.append(
                EventLogItem(
                    event_id=row[0],
                    user_id=row[1],
                    event_type=row[2],
                    timestamp=row[3],
                    session_id=row[4] or None,
                    page_url=row[5] or None,
                    referrer=row[6] or None,
                    user_agent=row[7] or None,
                    ip_address=row[8] or None,
                    properties=orjson.loads(row[9]) if row[9] else {},
                    ingested_at=row[10],
                )
            )

        return items, total

    async def get_event_by_id(self, event_id: str) -> EventLogItem | None:
        """根据 ID 获取事件"""
        sql = """
            SELECT
                event_id, user_id, event_type, timestamp,
                session_id, page_url, referrer, user_agent, ip_address,
                properties, ingested_at
            FROM event_logs
            WHERE event_id = {event_id: String}
        """
        result = self._client.query(sql, {"event_id": event_id})

        if not result.result_rows:
            return None

        row = result.result_rows[0]
        return EventLogItem(
            event_id=row[0],
            user_id=row[1],
            event_type=row[2],
            timestamp=row[3],
            session_id=row[4] or None,
            page_url=row[5] or None,
            referrer=row[6] or None,
            user_agent=row[7] or None,
            ip_address=row[8] or None,
            properties=orjson.loads(row[9]) if row[9] else {},
            ingested_at=row[10],
        )

    async def get_stats(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> EventStats:
        """获取事件统计"""
        conditions = []
        params: dict[str, Any] = {}

        if start_time:
            conditions.append("timestamp >= {start_time: DateTime64(3)}")
            params["start_time"] = start_time
        if end_time:
            conditions.append("timestamp <= {end_time: DateTime64(3)}")
            params["end_time"] = end_time

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # 按事件类型统计
        type_sql = f"""
            SELECT event_type, count() as count
            FROM event_logs
            WHERE {where_clause}
            GROUP BY event_type
            ORDER BY count DESC
        """
        type_result = self._client.query(type_sql, params)
        event_type_counts = {row[0]: row[1] for row in type_result.result_rows}

        # 总体统计
        total_sql = f"""
            SELECT
                count() as total_events,
                uniqExact(user_id) as unique_users,
                uniqExact(session_id) as unique_sessions
            FROM event_logs
            WHERE {where_clause}
        """
        total_result = self._client.query(total_sql, params)
        total_row = total_result.first_item

        return EventStats(
            total_events=total_row["total_events"],
            unique_users=total_row["unique_users"],
            unique_sessions=total_row["unique_sessions"],
            event_type_counts=event_type_counts,
        )

    def close(self) -> None:
        """关闭连接"""
        self._client.close()
