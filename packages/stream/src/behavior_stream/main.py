"""
BehaviorSense Stream Processor

使用 pulsar-client 消费事件，进行实时聚合和模式检测。
"""
import asyncio
import signal

from behavior_core.config.settings import get_settings
from behavior_core.utils.logging import get_logger, setup_logging

from behavior_stream.consumer import StreamConsumer
from behavior_stream.processor import StreamProcessor

settings = get_settings()
logger = get_logger(__name__)

# 全局状态
_running = False
_consumer: StreamConsumer | None = None
_processor: StreamProcessor | None = None


async def startup() -> None:
    """应用启动时的初始化"""
    global _consumer, _processor, _running

    print("=" * 60)
    print("BehaviorSense Stream Processor")
    print("=" * 60)
    print(f"Pulsar URL: {settings.pulsar_url}")
    print(f"Pulsar Topic: {settings.pulsar_topic('user-behavior')}")
    print("=" * 60)

    # 创建处理器
    _processor = StreamProcessor()

    # 创建消费者
    _consumer = StreamConsumer(
        pulsar_url=settings.pulsar_url,
        topic=settings.pulsar_topic("user-behavior"),
        subscription="stream-processor",
        processor=_processor,
    )

    # 启动消费者
    await _consumer.start()

    _running = True
    logger.info("Stream processor started")


async def shutdown() -> None:
    """应用关闭时的清理"""
    global _running

    logger.info("Shutting down stream processor...")
    _running = False

    if _consumer:
        await _consumer.stop()

    logger.info("Stream processor stopped")


async def run_forever() -> None:
    """主循环"""
    await startup()

    try:
        while _running:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await shutdown()


def main() -> None:
    """主入口"""
    setup_logging()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 信号处理
    def signal_handler():
        logger.info("Received shutdown signal")
        global _running
        _running = False

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows 不支持 add_signal_handler
            pass

    try:
        loop.run_until_complete(run_forever())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
