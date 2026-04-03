"""
模式检测任务

实现模式检测：
- 登录失败检测 (10分钟内失败5次)
- 高频操作检测
- 异常行为检测
- 输出到 alerts topic
"""
import asyncio
import orjson
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Any
import statistics

from behavior_stream.app import (
    app,
    user_behavior_topic,
    alerts_topic,
    user_login_failures,
    user_stats_table,
)
from behavior_stream.operators.window import SlidingWindow, SessionWindow
from behavior_core.models.event import UserBehavior, AlertEvent, EventType
from behavior_core.config.settings import get_settings

settings = get_settings()


# 检测配置
LOGIN_FAIL_THRESHOLD = 5  # 登录失败阈值
LOGIN_FAIL_WINDOW = timedelta(minutes=10)  # 登录失败时间窗口

HIGH_FREQUENCY_THRESHOLD = 100  # 高频操作阈值 (每分钟事件数)
HIGH_FREQUENCY_WINDOW = timedelta(minutes=1)  # 高频操作时间窗口

RAPID_CLICK_THRESHOLD = 20  # 快速点击阈值 (每10秒)
RAPID_CLICK_WINDOW = timedelta(seconds=10)  # 快速点击时间窗口

UNUSUAL_PURCHASE_THRESHOLD = 5  # 异常购买阈值 (同一商品重复购买)
UNUSUAL_PURCHASE_WINDOW = timedelta(hours=1)  # 异常购买时间窗口


# 内存中的检测状态
login_fail_counts: dict[str, list[datetime]] = defaultdict(list)
user_event_timestamps: dict[str, list[datetime]] = defaultdict(list)
user_click_timestamps: dict[str, list[datetime]] = defaultdict(list)
user_purchases: dict[str, dict[str, list[datetime]]] = defaultdict(lambda: defaultdict(list))


async def detect_login_failure(event: UserBehavior) -> AlertEvent | None:
    """
    检测登录失败

    规则: 10分钟内连续登录失败5次
    """
    if event.event_type != EventType.LOGIN:
        return None

    # 检查是否是登录失败
    login_status = event.properties.get("status", "")
    if login_status not in ["fail", "failed", "error"]:
        return None

    user_id = event.user_id
    now = event.timestamp

    # 记录失败时间
    login_fail_counts[user_id].append(now)

    # 清理过期记录
    cutoff = now - LOGIN_FAIL_WINDOW
    login_fail_counts[user_id] = [
        t for t in login_fail_counts[user_id] if t > cutoff
    ]

    # 检查是否达到阈值
    fail_count = len(login_fail_counts[user_id])
    if fail_count >= LOGIN_FAIL_THRESHOLD:
        # 创建告警
        alert = AlertEvent(
            alert_type="login_failure_brute_force",
            user_id=user_id,
            severity="high",
            message=f"检测到暴力破解尝试: 10分钟内登录失败 {fail_count} 次",
            trigger_data={
                "fail_count": fail_count,
                "window_minutes": 10,
                "threshold": LOGIN_FAIL_THRESHOLD,
                "last_failure_time": now.isoformat(),
            },
        )

        # 清空计数，避免重复告警
        login_fail_counts[user_id] = []

        return alert

    return None


async def detect_high_frequency(event: UserBehavior) -> AlertEvent | None:
    """
    检测高频操作

    规则: 每分钟操作数超过阈值
    """
    user_id = event.user_id
    now = event.timestamp

    # 记录事件时间
    user_event_timestamps[user_id].append(now)

    # 清理过期记录
    cutoff = now - HIGH_FREQUENCY_WINDOW
    user_event_timestamps[user_id] = [
        t for t in user_event_timestamps[user_id] if t > cutoff
    ]

    # 检查是否超过阈值
    event_count = len(user_event_timestamps[user_id])
    if event_count > HIGH_FREQUENCY_THRESHOLD:
        alert = AlertEvent(
            alert_type="high_frequency_operation",
            user_id=user_id,
            severity="medium",
            message=f"检测到高频操作: 每分钟 {event_count} 次事件",
            trigger_data={
                "event_count": event_count,
                "window_minutes": 1,
                "threshold": HIGH_FREQUENCY_THRESHOLD,
                "detection_time": now.isoformat(),
            },
        )

        return alert

    return None


async def detect_rapid_click(event: UserBehavior) -> AlertEvent | None:
    """
    检测快速点击

    规则: 10秒内点击超过阈值
    """
    if event.event_type != EventType.CLICK:
        return None

    user_id = event.user_id
    now = event.timestamp

    # 记录点击时间
    user_click_timestamps[user_id].append(now)

    # 清理过期记录
    cutoff = now - RAPID_CLICK_WINDOW
    user_click_timestamps[user_id] = [
        t for t in user_click_timestamps[user_id] if t > cutoff
    ]

    # 检查是否超过阈值
    click_count = len(user_click_timestamps[user_id])
    if click_count > RAPID_CLICK_THRESHOLD:
        alert = AlertEvent(
            alert_type="rapid_click",
            user_id=user_id,
            severity="low",
            message=f"检测到快速点击: 10秒内 {click_count} 次点击",
            trigger_data={
                "click_count": click_count,
                "window_seconds": 10,
                "threshold": RAPID_CLICK_THRESHOLD,
                "detection_time": now.isoformat(),
            },
        )

        return alert

    return None


async def detect_unusual_purchase(event: UserBehavior) -> AlertEvent | None:
    """
    检测异常购买行为

    规则: 1小时内同一商品重复购买超过阈值
    """
    if event.event_type != EventType.PURCHASE:
        return None

    user_id = event.user_id
    now = event.timestamp
    product_id = event.properties.get("product_id", "unknown")

    # 记录购买时间
    user_purchases[user_id][product_id].append(now)

    # 清理过期记录
    cutoff = now - UNUSUAL_PURCHASE_WINDOW
    user_purchases[user_id][product_id] = [
        t for t in user_purchases[user_id][product_id] if t > cutoff
    ]

    # 检查是否超过阈值
    purchase_count = len(user_purchases[user_id][product_id])
    if purchase_count > UNUSUAL_PURCHASE_THRESHOLD:
        alert = AlertEvent(
            alert_type="unusual_purchase_pattern",
            user_id=user_id,
            severity="medium",
            message=f"检测到异常购买: 1小时内购买商品 {product_id} 共 {purchase_count} 次",
            trigger_data={
                "product_id": product_id,
                "purchase_count": purchase_count,
                "window_hours": 1,
                "threshold": UNUSUAL_PURCHASE_THRESHOLD,
                "detection_time": now.isoformat(),
            },
        )

        return alert

    return None


async def detect_session_anomaly(event: UserBehavior) -> AlertEvent | None:
    """
    检测会话异常

    规则: 多设备同时登录或异常地理位置切换
    """
    if event.event_type not in [EventType.LOGIN, EventType.VIEW, EventType.CLICK]:
        return None

    user_id = event.user_id
    session_id = event.session_id
    ip_address = event.ip_address

    if not session_id or not ip_address:
        return None

    # 从用户统计中获取会话信息
    stats = user_stats_table.get(user_id, {})
    active_sessions = stats.get("active_sessions", {})

    # 检查是否有不同 IP 的活跃会话
    if session_id not in active_sessions:
        active_sessions[session_id] = {
            "ip_address": ip_address,
            "first_seen": event.timestamp.isoformat(),
            "last_seen": event.timestamp.isoformat(),
        }

        # 检查是否有来自不同 IP 的多个会话
        unique_ips = {s.get("ip_address") for s in active_sessions.values() if s.get("ip_address")}
        if len(unique_ips) > 1:
            alert = AlertEvent(
                alert_type="multi_ip_session",
                user_id=user_id,
                severity="medium",
                message=f"检测到多 IP 同时活跃: {unique_ips}",
                trigger_data={
                    "active_sessions": active_sessions,
                    "unique_ips": list(unique_ips),
                    "detection_time": event.timestamp.isoformat(),
                },
            )
            return alert

    # 更新会话信息
    active_sessions[session_id]["last_seen"] = event.timestamp.isoformat()
    stats["active_sessions"] = active_sessions
    user_stats_table[user_id] = stats

    return None


async def process_detection(event_data: dict[str, Any]) -> list[AlertEvent]:
    """处理事件进行模式检测"""
    alerts = []

    try:
        event = UserBehavior(**event_data)

        # 登录失败检测
        alert = await detect_login_failure(event)
        if alert:
            alerts.append(alert)

        # 高频操作检测
        alert = await detect_high_frequency(event)
        if alert:
            alerts.append(alert)

        # 快速点击检测
        alert = await detect_rapid_click(event)
        if alert:
            alerts.append(alert)

        # 异常购买检测
        alert = await detect_unusual_purchase(event)
        if alert:
            alerts.append(alert)

        # 会话异常检测
        alert = await detect_session_anomaly(event)
        if alert:
            alerts.append(alert)

    except Exception as e:
        print(f"Error in detection: {e}")

    return alerts


async def send_alert(alert: AlertEvent) -> None:
    """发送告警到 topic"""
    await alerts_topic.send(
        key=alert.user_id,
        value=orjson.dumps(alert.model_dump()).decode(),
    )
    print(f"Alert sent: {alert.alert_type} for user {alert.user_id}")


# Faust Agent: 模式检测
@app.agent(user_behavior_topic)
async def detection_agent(events: Any) -> None:
    """
    模式检测 Agent

    消费用户行为事件，进行实时模式检测。
    """
    async for event_str in events:
        try:
            event_data = orjson.loads(event_str)
            alerts = await process_detection(event_data)

            # 发送所有告警
            for alert in alerts:
                await send_alert(alert)

        except Exception as e:
            print(f"Error in detection agent: {e}")


# Faust Timer: 定期清理过期状态
@app.timer(interval=600.0)  # 每10分钟
async def cleanup_detection_state() -> None:
    """清理过期的检测状态"""
    now = datetime.utcnow()

    # 清理登录失败记录
    cutoff = now - LOGIN_FAIL_WINDOW
    for user_id in list(login_fail_counts.keys()):
        login_fail_counts[user_id] = [
            t for t in login_fail_counts[user_id] if t > cutoff
        ]
        if not login_fail_counts[user_id]:
            del login_fail_counts[user_id]

    # 清理事件时间戳
    cutoff = now - HIGH_FREQUENCY_WINDOW
    for user_id in list(user_event_timestamps.keys()):
        user_event_timestamps[user_id] = [
            t for t in user_event_timestamps[user_id] if t > cutoff
        ]
        if not user_event_timestamps[user_id]:
            del user_event_timestamps[user_id]

    # 清理点击时间戳
    cutoff = now - RAPID_CLICK_WINDOW
    for user_id in list(user_click_timestamps.keys()):
        user_click_timestamps[user_id] = [
            t for t in user_click_timestamps[user_id] if t > cutoff
        ]
        if not user_click_timestamps[user_id]:
            del user_click_timestamps[user_id]

    # 清理购买记录
    cutoff = now - UNUSUAL_PURCHASE_WINDOW
    for user_id in list(user_purchases.keys()):
        for product_id in list(user_purchases[user_id].keys()):
            user_purchases[user_id][product_id] = [
                t for t in user_purchases[user_id][product_id] if t > cutoff
            ]
            if not user_purchases[user_id][product_id]:
                del user_purchases[user_id][product_id]
        if not user_purchases[user_id]:
            del user_purchases[user_id]

    print("Detection state cleaned up")
