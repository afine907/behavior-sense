"""
流处理器

整合聚合和检测逻辑。
"""
import asyncio
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

import clickhouse_connect
import orjson
import pulsar
from behavior_core.config.settings import get_settings
from behavior_core.models.event import AggregationResult, AlertEvent, UserBehavior
from behavior_core.utils.logging import get_logger

from behavior_stream.operators.window import TumblingWindow

logger = get_logger(__name__)
settings = get_settings()


class BoundedStateDict:
    """有界状态字典 - 防止内存无限增长"""

    def __init__(self, max_users: int = 100000, max_events: int = 1000):
        self._data: dict[str, list[datetime]] = defaultdict(list)
        self._max_users = max_users
        self._max_events = max_events

    def append(self, user_id: str, timestamp: datetime) -> None:
        self._data[user_id].append(timestamp)
        if len(self._data[user_id]) > self._max_events:
            self._data[user_id] = self._data[user_id][-self._max_events:]
        if len(self._data) > self._max_users:
            users_to_remove = list(self._data.keys())[:self._max_users // 10]
            for uid in users_to_remove:
                del self._data[uid]

    def get(self, user_id: str) -> list[datetime]:
        return self._data.get(user_id, [])

    def set(self, user_id: str, value: list[datetime]) -> None:
        self._data[user_id] = value[-self._max_events:]

    def clear(self, user_id: str) -> None:
        if user_id in self._data:
            del self._data[user_id]

    def keys(self) -> list[str]:
        return list(self._data.keys())


class BoundedPurchaseDict:
    """有界购买记录字典"""

    def __init__(self, max_users: int = 100000, max_events: int = 1000):
        self._data: dict[str, dict[str, list[datetime]]] = defaultdict(lambda: defaultdict(list))
        self._max_users = max_users
        self._max_events = max_events

    def append(self, user_id: str, product_id: str, timestamp: datetime) -> None:
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


class StreamProcessor:
    """流处理器 - 整合聚合和检测"""

    # 检测配置
    LOGIN_FAIL_THRESHOLD = 5
    LOGIN_FAIL_WINDOW = timedelta(minutes=10)
    HIGH_FREQUENCY_THRESHOLD = 100
    HIGH_FREQUENCY_WINDOW = timedelta(minutes=1)
    RAPID_CLICK_THRESHOLD = 20
    RAPID_CLICK_WINDOW = timedelta(seconds=10)
    UNUSUAL_PURCHASE_THRESHOLD = 5
    UNUSUAL_PURCHASE_WINDOW = timedelta(hours=1)

    def __init__(self):
        # Pulsar 生产者（用于发送结果）
        self._client: pulsar.Client | None = None
        self._alert_producer: pulsar.Producer | None = None
        self._agg_producer: pulsar.Producer | None = None

        # ClickHouse 客户端（用于事件持久化）
        self._ch_client: clickhouse_connect.driver.Client | None = None

        # 聚合状态
        self._window_data: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "events": [],
            "event_count": 0,
            "view_count": 0,
            "click_count": 0,
            "purchase_count": 0,
            "total_amount": 0.0,
            "sessions": set(),
            "window_start": None,
        })
        self._minute_window = TumblingWindow[dict, dict](
            window_size=timedelta(minutes=1),
            allowed_lateness=timedelta(seconds=30),
        )
        self._user_stats: dict[str, dict[str, Any]] = {}

        # 检测状态
        self._login_fail_counts = BoundedStateDict()
        self._user_event_timestamps = BoundedStateDict()
        self._user_click_timestamps = BoundedStateDict()
        self._user_purchases = BoundedPurchaseDict()

        # 定时任务
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """启动处理器"""
        try:
            self._client = pulsar.Client(settings.pulsar_url)

            # 创建告警生产者
            self._alert_producer = self._client.create_producer(
                settings.pulsar_topic("alerts")
            )

            # 创建聚合结果生产者
            self._agg_producer = self._client.create_producer(
                settings.pulsar_topic("aggregation-result")
            )

            # 初始化 ClickHouse 客户端
            try:
                self._ch_client = clickhouse_connect.get_client(
                    host=settings.clickhouse_host,
                    port=settings.clickhouse_port,
                    username=settings.clickhouse_user,
                    password=settings.clickhouse_password.get_secret_value(),
                    database=settings.clickhouse_database,
                )
                logger.info("clickhouse_client_initialized")
            except Exception as e:
                logger.warning("clickhouse_client_init_failed", error=str(e))

            # 启动定时任务
            self._tasks = [
                asyncio.create_task(self._aggregation_timer()),
                asyncio.create_task(self._cleanup_timer()),
            ]

            logger.info("Processor started")

        except Exception as e:
            logger.error("Failed to start processor", error=str(e))
            raise

    async def stop(self) -> None:
        """停止处理器"""
        for task in self._tasks:
            task.cancel()

        if self._alert_producer:
            self._alert_producer.close()

        if self._agg_producer:
            self._agg_producer.close()

        if self._client:
            self._client.close()

        if self._ch_client:
            self._ch_client.close()
            logger.info("clickhouse_client_closed")

        logger.info("Processor stopped")

    async def process(self, event_data: dict[str, Any]) -> None:
        """处理事件"""
        try:
            event = UserBehavior(**event_data)

            # 写入 ClickHouse
            await self._write_to_clickhouse(event)

            # 聚合处理
            await self._process_aggregation(event_data)

            # 检测处理
            alerts = await self._process_detection(event)

            # 发送告警
            for alert in alerts:
                await self._send_alert(alert)

        except Exception as e:
            logger.error("Failed to process event", error=str(e))

    async def _write_to_clickhouse(self, event: UserBehavior) -> None:
        """写入事件到 ClickHouse"""
        if not self._ch_client:
            return

        try:
            event_type_value = (
                event.event_type.value
                if hasattr(event.event_type, "value")
                else str(event.event_type)
            )

            row = [
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

            self._ch_client.insert(
                "event_logs",
                [row],
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
        except Exception as e:
            logger.error("failed_to_write_clickhouse", error=str(e))

    # ==================== 聚合逻辑 ====================

    async def _process_aggregation(self, event_data: dict[str, Any]) -> None:
        """处理事件进行聚合"""
        try:
            event = UserBehavior(**event_data)
            user_id = event.user_id
            timestamp = event.timestamp

            # 更新分钟窗口
            window_start = self._minute_window.get_window_start(timestamp)
            window_key = f"{user_id}:{window_start.isoformat()}"

            # 初始化窗口数据
            if self._window_data[window_key]["window_start"] is None:
                self._window_data[window_key]["window_start"] = window_start

            # 累加统计
            window_data = self._window_data[window_key]
            window_data["events"].append(event_data)
            window_data["event_count"] += 1

            # 按事件类型统计
            event_type_str = (
                event.event_type.value
                if hasattr(event.event_type, 'value')
                else str(event.event_type)
            )
            if event_type_str == "view":
                window_data["view_count"] += 1
            elif event_type_str == "click":
                window_data["click_count"] += 1
            elif event_type_str == "purchase":
                window_data["purchase_count"] += 1
                amount = event.properties.get("amount", 0)
                if isinstance(amount, (int, float)):
                    window_data["total_amount"] += amount

            # 会话统计
            if event.session_id:
                window_data["sessions"].add(event.session_id)

            # 更新全局用户统计
            stats = self._user_stats.get(user_id, {})
            stats["total_events"] = stats.get("total_events", 0) + 1
            stats["last_event_time"] = timestamp.isoformat()
            stats["last_event_type"] = event_type_str
            self._user_stats[user_id] = stats

        except Exception as e:
            logger.error("Error in aggregation", error=str(e))

    async def _flush_expired_windows(self) -> None:
        """刷新过期的窗口"""
        now = datetime.now(UTC)
        expired_keys = []

        for window_key, data in self._window_data.items():
            if data["window_start"] is None:
                continue

            window_start = data["window_start"]
            window_end = window_start + timedelta(minutes=1)

            # 窗口已过期
            if now > window_end + timedelta(seconds=30):
                user_id = window_key.split(":")[0]
                await self._emit_aggregation_result(user_id, window_start, window_end, data)
                expired_keys.append(window_key)

        # 清理已处理的窗口
        for key in expired_keys:
            del self._window_data[key]

    async def _emit_aggregation_result(
        self,
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

        if self._agg_producer:
            self._agg_producer.send(
                orjson.dumps(result.model_dump()),
                partition_key=user_id,
            )

    async def _aggregation_timer(self) -> None:
        """每分钟聚合定时器"""
        while True:
            await asyncio.sleep(60)
            await self._flush_expired_windows()
            logger.debug("Aggregation timer triggered")

    # ==================== 检测逻辑 ====================

    async def _process_detection(self, event: UserBehavior) -> list[AlertEvent]:
        """处理事件进行模式检测"""
        alerts = []

        # 登录失败检测
        alert = await self._detect_login_failure(event)
        if alert:
            alerts.append(alert)

        # 高频操作检测
        alert = await self._detect_high_frequency(event)
        if alert:
            alerts.append(alert)

        # 快速点击检测
        alert = await self._detect_rapid_click(event)
        if alert:
            alerts.append(alert)

        # 异常购买检测
        alert = await self._detect_unusual_purchase(event)
        if alert:
            alerts.append(alert)

        return alerts

    async def _detect_login_failure(self, event: UserBehavior) -> AlertEvent | None:
        """检测登录失败"""
        event_type_str = (
            event.event_type.value
            if hasattr(event.event_type, 'value')
            else str(event.event_type)
        )
        if event_type_str != "login":
            return None

        login_status = event.properties.get("status", "")
        if login_status not in ["fail", "failed", "error"]:
            return None

        user_id = event.user_id
        now = event.timestamp

        self._login_fail_counts.append(user_id, now)

        cutoff = now - self.LOGIN_FAIL_WINDOW
        timestamps = self._login_fail_counts.get(user_id)
        filtered = [t for t in timestamps if t > cutoff]
        self._login_fail_counts.set(user_id, filtered)

        fail_count = len(filtered)
        if fail_count >= self.LOGIN_FAIL_THRESHOLD:
            alert = AlertEvent(
                alert_type="login_failure_brute_force",
                user_id=user_id,
                severity="high",
                message=f"检测到暴力破解尝试: 10分钟内登录失败 {fail_count} 次",
                trigger_data={
                    "fail_count": fail_count,
                    "window_minutes": 10,
                    "threshold": self.LOGIN_FAIL_THRESHOLD,
                },
            )
            self._login_fail_counts.clear(user_id)
            return alert

        return None

    async def _detect_high_frequency(self, event: UserBehavior) -> AlertEvent | None:
        """检测高频操作"""
        user_id = event.user_id
        now = event.timestamp

        self._user_event_timestamps.append(user_id, now)

        cutoff = now - self.HIGH_FREQUENCY_WINDOW
        timestamps = self._user_event_timestamps.get(user_id)
        filtered = [t for t in timestamps if t > cutoff]
        self._user_event_timestamps.set(user_id, filtered)

        event_count = len(filtered)
        if event_count > self.HIGH_FREQUENCY_THRESHOLD:
            return AlertEvent(
                alert_type="high_frequency_operation",
                user_id=user_id,
                severity="medium",
                message=f"检测到高频操作: 每分钟 {event_count} 次事件",
                trigger_data={
                    "event_count": event_count,
                    "threshold": self.HIGH_FREQUENCY_THRESHOLD,
                },
            )

        return None

    async def _detect_rapid_click(self, event: UserBehavior) -> AlertEvent | None:
        """检测快速点击"""
        event_type_str = (
            event.event_type.value
            if hasattr(event.event_type, 'value')
            else str(event.event_type)
        )
        if event_type_str != "click":
            return None

        user_id = event.user_id
        now = event.timestamp

        self._user_click_timestamps.append(user_id, now)

        cutoff = now - self.RAPID_CLICK_WINDOW
        timestamps = self._user_click_timestamps.get(user_id)
        filtered = [t for t in timestamps if t > cutoff]
        self._user_click_timestamps.set(user_id, filtered)

        click_count = len(filtered)
        if click_count > self.RAPID_CLICK_THRESHOLD:
            return AlertEvent(
                alert_type="rapid_click",
                user_id=user_id,
                severity="low",
                message=f"检测到快速点击: 10秒内 {click_count} 次点击",
                trigger_data={
                    "click_count": click_count,
                    "threshold": self.RAPID_CLICK_THRESHOLD,
                },
            )

        return None

    async def _detect_unusual_purchase(self, event: UserBehavior) -> AlertEvent | None:
        """检测异常购买"""
        event_type_str = (
            event.event_type.value
            if hasattr(event.event_type, 'value')
            else str(event.event_type)
        )
        if event_type_str != "purchase":
            return None

        user_id = event.user_id
        now = event.timestamp
        product_id = event.properties.get("product_id", "unknown")

        self._user_purchases.append(user_id, product_id, now)

        cutoff = now - self.UNUSUAL_PURCHASE_WINDOW
        user_product_purchases = self._user_purchases.get(user_id)
        if product_id in user_product_purchases:
            filtered = [t for t in user_product_purchases[product_id] if t > cutoff]
            user_product_purchases[product_id] = filtered

        purchase_count = len(self._user_purchases.get(user_id).get(product_id, []))
        if purchase_count > self.UNUSUAL_PURCHASE_THRESHOLD:
            return AlertEvent(
                alert_type="unusual_purchase_pattern",
                user_id=user_id,
                severity="medium",
                message=f"检测到异常购买: 1小时内购买商品 {product_id} 共 {purchase_count} 次",
                trigger_data={
                    "product_id": product_id,
                    "purchase_count": purchase_count,
                    "threshold": self.UNUSUAL_PURCHASE_THRESHOLD,
                },
            )

        return None

    async def _send_alert(self, alert: AlertEvent) -> None:
        """发送告警"""
        if self._alert_producer:
            self._alert_producer.send(
                orjson.dumps(alert.model_dump()),
                partition_key=alert.user_id,
            )
            logger.info(
                "Alert sent",
                alert_type=alert.alert_type,
                user_id=alert.user_id,
            )

    async def _cleanup_timer(self) -> None:
        """定期清理过期状态"""
        while True:
            await asyncio.sleep(600)  # 每10分钟

            now = datetime.now(UTC)

            # 清理登录失败记录
            cutoff = now - self.LOGIN_FAIL_WINDOW
            for user_id in self._login_fail_counts.keys():
                timestamps = self._login_fail_counts.get(user_id)
                filtered = [t for t in timestamps if t > cutoff]
                if filtered:
                    self._login_fail_counts.set(user_id, filtered)
                else:
                    self._login_fail_counts.clear(user_id)

            # 清理事件时间戳
            cutoff = now - self.HIGH_FREQUENCY_WINDOW
            for user_id in self._user_event_timestamps.keys():
                timestamps = self._user_event_timestamps.get(user_id)
                filtered = [t for t in timestamps if t > cutoff]
                if filtered:
                    self._user_event_timestamps.set(user_id, filtered)
                else:
                    self._user_event_timestamps.clear(user_id)

            logger.debug("Cleanup timer triggered")
