"""
Pulsar 消费者

使用 pulsar-client 消费用户行为事件。
"""
import asyncio
from datetime import datetime, timezone
from typing import Any, Callable

import orjson
import pulsar
from behavior_core.utils.logging import get_logger

logger = get_logger(__name__)


class StreamConsumer:
    """Pulsar 消费者"""

    def __init__(
        self,
        pulsar_url: str,
        topic: str,
        subscription: str,
        processor: Any,
    ):
        self._pulsar_url = pulsar_url
        self._topic = topic
        self._subscription = subscription
        self._processor = processor
        self._client: pulsar.Client | None = None
        self._consumer: pulsar.Consumer | None = None
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """启动消费者"""
        try:
            # 创建 Pulsar 客户端
            self._client = pulsar.Client(self._pulsar_url)

            # 创建消费者
            self._consumer = self._client.subscribe(
                self._topic,
                self._subscription,
                consumer_type=pulsar.ConsumerType.Shared,
            )

            self._running = True

            # 启动消费任务
            self._task = asyncio.create_task(self._consume_loop())

            logger.info(
                "Consumer started",
                topic=self._topic,
                subscription=self._subscription,
            )

        except Exception as e:
            logger.error("Failed to start consumer", error=str(e))
            raise

    async def stop(self) -> None:
        """停止消费者"""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self._consumer:
            self._consumer.close()

        if self._client:
            self._client.close()

        logger.info("Consumer stopped")

    async def _consume_loop(self) -> None:
        """消费循环"""
        while self._running:
            try:
                # 非阻塞获取消息
                msg = self._consumer.receive(timeout_millis=1000)

                if msg:
                    try:
                        # 解析消息
                        event_data = orjson.loads(msg.data())

                        # 处理消息
                        await self._processor.process(event_data)

                        # 确认消息
                        self._consumer.acknowledge(msg)

                    except orjson.JSONDecodeError as e:
                        logger.warning("Failed to parse message", error=str(e))
                        self._consumer.negative_acknowledge(msg)

                    except Exception as e:
                        logger.error("Failed to process message", error=str(e))
                        self._consumer.negative_acknowledge(msg)

            except pulsar.PulsarException:
                # 超时，继续循环
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error("Consumer error", error=str(e))
                await asyncio.sleep(1)
