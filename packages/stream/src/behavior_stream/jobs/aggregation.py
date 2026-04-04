"""
聚合任务

实现窗口聚合：
- 每分钟聚合统计
- 用户事件计数
- 购买金额统计
- 输出到 aggregation-result topic
"""
import asyncio
import orjson
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Any

from behavior_stream.app import (
    app,
    user_behavior_topic,
    aggregation_result_topic,
    user_stats_table,
)
from behavior_stream.operators.window import TumblingWindow, WindowAggregator
from behavior_core.models.event import UserBehavior, AggregationResult, EventType
from behavior_core.config.settings import get_settings

settings = get_settings()


# 内存中的窗口状态 (用于当前窗口聚合)
current_window_data: dict[str, dict[str, Any]] = defaultdict(lambda: {
    "events": [],
    "event_count": 0,
    "view_count": 0,
    "click_count": 0,
    "purchase_count": 0,
    "total_amount": 0.0,
    "sessions": set(),
    "window_start": None,
})

# 滚动窗口 (1分钟)
minute_window = TumblingWindow[dict](
    window_size=timedelta(minutes=1),
    allowed_lateness=timedelta(seconds=30),
)


async def process_event_for_aggregation(event_data: dict[str, Any]) -> None:
    """处理事件进行聚合"""
    try:
        # 解析事件
        event = UserBehavior(**event_data)
        user_id = event.user_id
        timestamp = event.timestamp

        # 更新分钟窗口
        window_start = minute_window.get_window_start(timestamp)
        window_key = f"{user_id}:{window_start.isoformat()}"

        # 初始化窗口数据
        if current_window_data[window_key]["window_start"] is None:
            current_window_data[window_key]["window_start"] = window_start

        # 累加统计
        window_data = current_window_data[window_key]
        window_data["events"].append(event_data)
        window_data["event_count"] += 1

        # 按事件类型统计
        event_type = event.event_type
        if event_type == EventType.VIEW:
            window_data["view_count"] += 1
        elif event_type == EventType.CLICK:
            window_data["click_count"] += 1
        elif event_type == EventType.PURCHASE:
            window_data["purchase_count"] += 1
            amount = event.properties.get("amount", 0)
            if isinstance(amount, (int, float)):
                window_data["total_amount"] += amount

        # 会话统计
        if event.session_id:
            window_data["sessions"].add(event.session_id)

        # 更新全局用户统计表
        stats = user_stats_table.get(user_id, {})
        stats["total_events"] = stats.get("total_events", 0) + 1
        stats["last_event_time"] = timestamp.isoformat()
        stats["last_event_type"] = event_type
        user_stats_table[user_id] = stats

    except Exception as e:
        print(f"Error processing event for aggregation: {e}")


async def emit_aggregation_result(
    user_id: str,
    window_start: datetime,
    window_end: datetime,
    data: dict[str, Any],
) -> None:
    """发送聚合结果"""
    result = AggregationResult(
        user_id=user_id,
        window_start=window_start,
        window_end=window_end,
        event_count=data["event_count"],
        view_count=data["view_count"],
        click_count=data["click_count"],
        purchase_count=data["purchase_count"],
        total_amount=data["total_amount"],
        unique_sessions=len(data["sessions"]),
    )

    # 发送到聚合结果 topic
    await aggregation_result_topic.send(
        key=user_id,
        value=orjson.dumps(result.model_dump()).decode(),
    )


async def flush_expired_windows() -> None:
    """刷新过期的窗口，发送聚合结果"""
    now = datetime.utcnow()
    expired_keys = []

    for window_key, data in current_window_data.items():
        if data["window_start"] is None:
            continue

        window_start = data["window_start"]
        window_end = window_start + timedelta(minutes=1)

        # 窗口已过期 (当前时间超过窗口结束时间 + 允许延迟)
        if now > window_end + timedelta(seconds=30):
            # 提取 user_id
            user_id = window_key.split(":")[0]

            # 发送聚合结果
            await emit_aggregation_result(user_id, window_start, window_end, data)
            expired_keys.append(window_key)

    # 清理已处理的窗口
    for key in expired_keys:
        del current_window_data[key]


async def aggregate_global_stats() -> dict[str, Any]:
    """聚合全局统计"""
    global_stats = {
        "total_users": len(user_stats_table),
        "total_events": sum(
            stats.get("total_events", 0)
            for stats in user_stats_table.values()
        ),
        "timestamp": datetime.utcnow().isoformat(),
    }
    return global_stats


# Faust Agent: 处理用户行为事件
@app.agent(user_behavior_topic)
async def aggregation_agent(events: Any) -> None:
    """
    聚合处理 Agent

    消费用户行为事件，进行实时聚合统计。
    """
    async for event_str in events:
        try:
            event_data = orjson.loads(event_str)
            await process_event_for_aggregation(event_data)
        except Exception as e:
            print(f"Error in aggregation agent: {e}")


# Faust Timer: 每分钟触发窗口刷新
@app.timer(interval=60.0)
async def minute_aggregation_timer() -> None:
    """
    每分钟聚合定时器

    刷新过期的窗口并发送聚合结果。
    """
    await flush_expired_windows()

    # 可选：发送全局统计
    global_stats = await aggregate_global_stats()
    print(f"Global stats: {global_stats}")


# Faust Timer: 每5分钟清理状态
@app.timer(interval=300.0)
async def cleanup_timer() -> None:
    """清理过期状态"""
    cleaned = minute_window.cleanup()
    if cleaned > 0:
        print(f"Cleaned {cleaned} expired windows")
