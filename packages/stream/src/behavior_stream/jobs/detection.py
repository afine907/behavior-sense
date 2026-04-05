"""
模式检测任务

实现模式检测：
- 登录失败检测 (10分钟内失败5次)
- 高频操作检测
- 异常行为检测
- 输出到 alerts topic
"""
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import orjson
from behavior_core.config.settings import get_settings
from behavior_core.models.event import AlertEvent, EventType, UserBehavior

from behavior_stream.app import (
    alerts_topic,
    app,
    user_behavior_topic,
    user_stats_table,
)

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

# 内存保护配置 - 防止内存泄漏
MAX_USERS_IN_MEMORY = 100000  # 最大用户数限制
MAX_EVENTS_PER_USER = 1000  # 每个用户最大事件数限制


class BoundedStateDict:
    """有界状态字典 - 防止内存无限增长"""

    def __init__(self, max_users: int = MAX_USERS_IN_MEMORY, max_events: int = MAX_EVENTS_PER_USER):
        self._data: dict[str, list[datetime]] = defaultdict(list)
        self._max_users = max_users
        self._max_events = max_events
        self._lock = asyncio.Lock()

    def append(self, user_id: str, timestamp: datetime) -> None:
        """添加事件时间戳"""
        self._data[user_id].append(timestamp)
        # 限制每个用户的事件数
        if len(self._data[user_id]) > self._max_events:
            self._data[user_id] = self._data[user_id][-self._max_events:]
        # 如果用户数超限，清理最老的用户的记录
        if len(self._data) > self._max_users:
            # 移除最早的 10% 用户
            users_to_remove = list(self._data.keys())[:self._max_users // 10]
            for uid in users_to_remove:
                del self._data[uid]

    def get(self, user_id: str) -> list[datetime]:
        return self._data.get(user_id, [])

    def set(self, user_id: str, value: list[datetime]) -> None:
        self._data[user_id] = value[-self._max_events:]  # 限制长度

    def clear(self, user_id: str) -> None:
        if user_id in self._data:
            del self._data[user_id]

    def keys(self) -> list[str]:
        return list(self._data.keys())

    def __contains__(self, user_id: str) -> bool:
        return user_id in self._data

    def __len__(self) -> int:
        return len(self._data)


class BoundedPurchaseDict:
    """有界购买记录字典"""

    def __init__(self, max_users: int = MAX_USERS_IN_MEMORY, max_events: int = MAX_EVENTS_PER_USER):
        self._data: dict[str, dict[str, list[datetime]]] = defaultdict(lambda: defaultdict(list))
        self._max_users = max_users
        self._max_events = max_events

    def append(self, user_id: str, product_id: str, timestamp: datetime) -> None:
        """添加购买时间戳"""
        self._data[user_id][product_id].append(timestamp)
        if len(self._data[user_id][product_id]) > self._max_events:
            self._data[user_id][product_id] = self._data[user_id][product_id][-self._max_events:]
        if len(self._data) > self._max_users:
            users_to_remove = list(self._data.keys())[:self._max_users // 10]
            for uid in users_to_remove:
                del self._data[uid]

    def get(self, user_id: str) -> dict[str, list[datetime]]:
        return self._data.get(user_id, defaultdict(list))

    def keys(self) -> list[str]:
        return list(self._data.keys())

    def __contains__(self, user_id: str) -> bool:
        return user_id in self._data


# 内存中的检测状态 - 使用有界字典防止内存泄漏
login_fail_counts = BoundedStateDict()
user_event_timestamps = BoundedStateDict()
user_click_timestamps = BoundedStateDict()
user_purchases = BoundedPurchaseDict()


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
    login_fail_counts.append(user_id, now)

    # 清理过期记录
    cutoff = now - LOGIN_FAIL_WINDOW
    timestamps = login_fail_counts.get(user_id)
    filtered = [t for t in timestamps if t > cutoff]
    login_fail_counts.set(user_id, filtered)

    # 检查是否达到阈值
    fail_count = len(filtered)
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
        login_fail_counts.clear(user_id)

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
    user_event_timestamps.append(user_id, now)

    # 清理过期记录
    cutoff = now - HIGH_FREQUENCY_WINDOW
    timestamps = user_event_timestamps.get(user_id)
    filtered = [t for t in timestamps if t > cutoff]
    user_event_timestamps.set(user_id, filtered)

    # 检查是否超过阈值
    event_count = len(filtered)
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
    user_click_timestamps.append(user_id, now)

    # 清理过期记录
    cutoff = now - RAPID_CLICK_WINDOW
    timestamps = user_click_timestamps.get(user_id)
    filtered = [t for t in timestamps if t > cutoff]
    user_click_timestamps.set(user_id, filtered)

    # 检查是否超过阈值
    click_count = len(filtered)
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
    user_purchases.append(user_id, product_id, now)

    # 清理过期记录
    cutoff = now - UNUSUAL_PURCHASE_WINDOW
    user_product_purchases = user_purchases.get(user_id)
    if product_id in user_product_purchases:
        filtered = [t for t in user_product_purchases[product_id] if t > cutoff]
        user_product_purchases[product_id] = filtered

    # 检查是否超过阈值
    purchase_count = len(user_purchases.get(user_id).get(product_id, []))
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
    now = datetime.now(timezone.utc)

    # 清理登录失败记录
    cutoff = now - LOGIN_FAIL_WINDOW
    for user_id in login_fail_counts.keys():
        timestamps = login_fail_counts.get(user_id)
        filtered = [t for t in timestamps if t > cutoff]
        if filtered:
            login_fail_counts.set(user_id, filtered)
        else:
            login_fail_counts.clear(user_id)

    # 清理事件时间戳
    cutoff = now - HIGH_FREQUENCY_WINDOW
    for user_id in user_event_timestamps.keys():
        timestamps = user_event_timestamps.get(user_id)
        filtered = [t for t in timestamps if t > cutoff]
        if filtered:
            user_event_timestamps.set(user_id, filtered)
        else:
            user_event_timestamps.clear(user_id)

    # 清理点击时间戳
    cutoff = now - RAPID_CLICK_WINDOW
    for user_id in user_click_timestamps.keys():
        timestamps = user_click_timestamps.get(user_id)
        filtered = [t for t in timestamps if t > cutoff]
        if filtered:
            user_click_timestamps.set(user_id, filtered)
        else:
            user_click_timestamps.clear(user_id)

    # 清理购买记录
    cutoff = now - UNUSUAL_PURCHASE_WINDOW
    for user_id in user_purchases.keys():
        user_products = user_purchases.get(user_id)
        for product_id in list(user_products.keys()):
            filtered = [t for t in user_products[product_id] if t > cutoff]
            if filtered:
                user_products[product_id] = filtered
            else:
                del user_products[product_id]

    print("Detection state cleaned up")
