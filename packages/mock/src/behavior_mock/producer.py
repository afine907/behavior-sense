"""
Pulsar 消息生产者

负责将用户行为事件发送到 Pulsar 消息队列。
"""
import asyncio
from typing import Callable
import pulsar
import orjson
from behavior_core.models.event import UserBehavior
from behavior_core.config.settings import get_settings
from behavior_core.utils.logging import get_logger

logger = get_logger(__name__)


class PulsarProducer:
    """Pulsar 消息生产者"""

    def __init__(
        self,
        service_url: str | None = None,
        topic: str | None = None,
        batching_enabled: bool = True,
        batching_max_messages: int = 1000,
        batching_max_publish_delay_ms: int = 10,
    ):
        """
        初始化 Pulsar 生产者

        Args:
            service_url: Pulsar 服务地址
            topic: 目标 Topic
            batching_enabled: 是否启用批处理
            batching_max_messages: 批处理最大消息数
            batching_max_publish_delay_ms: 批处理最大延迟(毫秒)
        """
        settings = get_settings()
        self.service_url = service_url or settings.pulsar_url
        self.topic = topic or settings.pulsar_topic("user-behavior")
        self.batching_enabled = batching_enabled
        self.batching_max_messages = batching_max_messages
        self.batching_max_publish_delay_ms = batching_max_publish_delay_ms

        self._client: pulsar.Client | None = None
        self._producer: pulsar.Producer | None = None

        logger.info(
            "pulsar_producer_initialized",
            service_url=self.service_url,
            topic=self.topic,
        )

    def connect(self) -> None:
        """建立 Pulsar 连接"""
        if self._producer is not None:
            logger.warning("producer_already_connected")
            return

        try:
            self._client = pulsar.Client(self.service_url)
            self._producer = self._client.create_producer(
                self.topic,
                batching_enabled=self.batching_enabled,
                batching_max_messages=self.batching_max_messages,
                batching_max_publish_delay_ms=self.batching_max_publish_delay_ms,
            )
            logger.info("pulsar_producer_connected", topic=self.topic)
        except Exception as e:
            logger.error("pulsar_connection_failed", error=str(e))
            raise

    def send(
        self,
        event: UserBehavior,
        callback: Callable[[pulsar.Result, pulsar.MessageId], None] | None = None,
    ) -> pulsar.MessageId | None:
        """
        发送事件到 Pulsar

        Args:
            event: 用户行为事件
            callback: 发送完成回调(异步模式)

        Returns:
            消息ID(同步模式)，异步模式返回 None
        """
        if self._producer is None:
            raise RuntimeError("Producer not connected. Call connect() first.")

        try:
            # 使用 orjson 进行高效序列化
            data = orjson.dumps(event.model_dump())
            event_timestamp = int(event.timestamp.timestamp() * 1000)

            if callback:
                # 异步发送
                self._producer.send_async(
                    data,
                    callback,
                    event.event_id.encode(),
                    event_timestamp=event_timestamp,
                )
                return None
            else:
                # 同步发送
                message_id = self._producer.send(
                    data,
                    event.event_id.encode(),
                    event_timestamp=event_timestamp,
                )
                logger.debug(
                    "event_sent",
                    event_id=event.event_id,
                    message_id=str(message_id),
                )
                return message_id

        except Exception as e:
            logger.error(
                "send_event_failed",
                event_id=event.event_id,
                error=str(e),
            )
            raise

    async def send_async(self, event: UserBehavior) -> pulsar.MessageId:
        """
        异步发送事件

        Args:
            event: 用户行为事件

        Returns:
            消息ID
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send, event)

    def send_batch(self, events: list[UserBehavior]) -> list[pulsar.MessageId]:
        """
        批量发送事件

        Args:
            events: 用户行为事件列表

        Returns:
            消息ID列表
        """
        if self._producer is None:
            raise RuntimeError("Producer not connected. Call connect() first.")

        message_ids = []
        for event in events:
            message_id = self.send(event)
            if message_id:
                message_ids.append(message_id)

        logger.info("batch_sent", count=len(events))
        return message_ids

    async def send_batch_async(self, events: list[UserBehavior]) -> list[pulsar.MessageId]:
        """
        异步批量发送事件

        Args:
            events: 用户行为事件列表

        Returns:
            消息ID列表
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send_batch, events)

    def flush(self) -> None:
        """刷新待发送的消息"""
        if self._producer:
            self._producer.flush()
            logger.debug("producer_flushed")

    def close(self) -> None:
        """关闭 Pulsar 连接"""
        if self._producer:
            try:
                self._producer.flush()
                self._producer.close()
                logger.info("producer_closed")
            except Exception as e:
                logger.error("close_producer_failed", error=str(e))
            finally:
                self._producer = None

        if self._client:
            try:
                self._client.close()
                logger.info("client_closed")
            except Exception as e:
                logger.error("close_client_failed", error=str(e))
            finally:
                self._client = None

    def __enter__(self) -> "PulsarProducer":
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口"""
        self.close()


class MockProducer:
    """模拟生产者(用于测试)"""

    def __init__(self):
        """初始化模拟生产者"""
        self._events: list[UserBehavior] = []
        self._connected = False
        logger.info("mock_producer_initialized")

    def connect(self) -> None:
        """建立连接"""
        self._connected = True
        logger.info("mock_producer_connected")

    def send(self, event: UserBehavior) -> str:
        """发送事件"""
        if not self._connected:
            raise RuntimeError("Producer not connected")
        self._events.append(event)
        logger.debug("mock_event_sent", event_id=event.event_id)
        return f"mock-msg-{len(self._events)}"

    async def send_async(self, event: UserBehavior) -> str:
        """异步发送事件"""
        return self.send(event)

    def close(self) -> None:
        """关闭连接"""
        self._connected = False
        logger.info("mock_producer_closed")

    @property
    def events(self) -> list[UserBehavior]:
        """获取已发送的事件列表"""
        return self._events.copy()

    @property
    def event_count(self) -> int:
        """获取已发送事件数量"""
        return len(self._events)

    def clear(self) -> None:
        """清空已发送的事件"""
        self._events.clear()
