"""
behavior_stream 入口

启动 Faust worker，注册所有任务。
"""
import asyncio
import sys
from typing import Any

from behavior_stream.app import app
from behavior_stream.jobs import aggregation, detection
from behavior_core.config.settings import get_settings

settings = get_settings()


async def startup() -> None:
    """应用启动时的初始化"""
    print("=" * 60)
    print("BehaviorSense Stream Processor")
    print("=" * 60)
    print(f"Pulsar URL: {settings.pulsar_url}")
    print(f"Pulsar Topic Base: {settings.pulsar_topic_base}")
    print(f"App ID: {app.id}")
    print("=" * 60)


async def shutdown() -> None:
    """应用关闭时的清理"""
    print("Shutting down stream processor...")


def main() -> None:
    """
    主入口

    启动 Faust worker。
    """
    import faust

    # 注册启动和关闭钩子
    app.on_startup.connect(lambda *_: startup())
    app.on_shutdown.connect(lambda *_: shutdown())

    # 启动 worker
    # 使用命令行参数或默认配置
    worker = faust.Worker(
        app,
        loglevel="INFO",
        logfile=None,  # 输出到控制台
    )

    # 运行 worker
    worker.execute_from_commandline()


if __name__ == "__main__":
    main()
