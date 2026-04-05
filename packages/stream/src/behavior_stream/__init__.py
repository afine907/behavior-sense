"""
behavior_stream 模块

实时流处理模块，基于 pulsar-client 实现用户行为数据的实时处理。
"""
from behavior_stream.consumer import StreamConsumer
from behavior_stream.processor import StreamProcessor

__all__ = ["StreamConsumer", "StreamProcessor"]
