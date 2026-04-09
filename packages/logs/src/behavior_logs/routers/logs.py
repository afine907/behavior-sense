"""
事件日志 API 路由
"""
from datetime import UTC, datetime

from behavior_core.utils.logging import get_logger
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from behavior_logs.repositories.event_repo import (
    EventLogItem,
    EventLogListResponse,
    EventLogQuery,
    EventLogRepository,
    EventStats,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/logs", tags=["logs"])


# ============== 健康检查 ==============


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str
    timestamp: datetime
    clickhouse_connected: bool


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """健康检查"""
    clickhouse_connected = False
    try:
        repo = EventLogRepository()
        repo._client.query("SELECT 1")
        clickhouse_connected = True
        repo.close()
    except Exception as e:
        logger.warning("clickhouse_health_check_failed", error=str(e))

    return HealthResponse(
        status="healthy" if clickhouse_connected else "degraded",
        timestamp=datetime.now(UTC),
        clickhouse_connected=clickhouse_connected,
    )


# ============== 依赖注入 ==============


def get_repository() -> EventLogRepository:
    """获取仓库实例"""
    return EventLogRepository()


# ============== 事件查询 ==============


@router.get("/events", response_model=EventLogListResponse)
async def list_events(
    user_id: str | None = Query(default=None, description="用户ID"),
    event_type: str | None = Query(default=None, description="事件类型"),
    session_id: str | None = Query(default=None, description="会话ID"),
    start_time: datetime | None = Query(
        default=None, description="开始时间 (ISO 8601)"
    ),
    end_time: datetime | None = Query(
        default=None, description="结束时间 (ISO 8601)"
    ),
    page_url: str | None = Query(
        default=None, description="页面URL (支持模糊匹配)"
    ),
    ip_address: str | None = Query(default=None, description="IP地址"),
    page: int = Query(default=1, ge=1, description="页码"),
    size: int = Query(default=50, ge=1, le=200, description="每页数量"),
    sort_order: str = Query(default="desc", description="排序方向 (asc/desc)"),
    repo: EventLogRepository = Depends(get_repository),
) -> EventLogListResponse:
    """
    查询事件日志列表

    支持多条件过滤、分页、排序。
    时间格式: ISO 8601 (如 2024-01-01T00:00:00Z)
    """
    query = EventLogQuery(
        user_id=user_id,
        event_type=event_type,
        session_id=session_id,
        start_time=start_time,
        end_time=end_time,
        page_url=page_url,
        ip_address=ip_address,
        page=page,
        size=size,
        sort_order=sort_order,
    )

    items, total = await repo.query_events(query)

    return EventLogListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.get("/events/{event_id}", response_model=EventLogItem)
async def get_event(
    event_id: str,
    repo: EventLogRepository = Depends(get_repository),
) -> EventLogItem:
    """
    获取事件详情
    """
    event = await repo.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/stats", response_model=EventStats)
async def get_stats(
    start_time: datetime | None = Query(default=None, description="开始时间"),
    end_time: datetime | None = Query(default=None, description="结束时间"),
    repo: EventLogRepository = Depends(get_repository),
) -> EventStats:
    """
    获取事件统计

    返回事件总数、独立用户数、独立会话数、按类型分布。
    """
    return await repo.get_stats(start_time, end_time)
