"""
behavior_mock 模块单元测试
"""
import pytest
from datetime import datetime

from behavior_core.models.event import EventType
from behavior_mock.generator import BehaviorGenerator, WeightedBehaviorGenerator


class TestBehaviorGenerator:
    """用户行为生成器测试"""

    def test_create_generator(self):
        """测试创建生成器"""
        generator = BehaviorGenerator(user_pool_size=100)
        assert generator.user_pool_size == 100
        assert len(generator.event_types) == len(EventType)

    def test_create_generator_with_seed(self):
        """测试带随机种子的生成器"""
        generator1 = BehaviorGenerator(user_pool_size=100, seed=42)
        generator2 = BehaviorGenerator(user_pool_size=100, seed=42)

        event1 = generator1.generate()
        event2 = generator2.generate()

        # 相同种子应生成相同的 user_id
        assert event1.user_id == event2.user_id

    def test_create_generator_with_custom_event_types(self):
        """测试自定义事件类型"""
        custom_types = [EventType.VIEW, EventType.CLICK, EventType.PURCHASE]
        generator = BehaviorGenerator(
            user_pool_size=100,
            event_types=custom_types
        )
        assert generator.event_types == custom_types

    def test_generate_single_event(self):
        """测试生成单个事件"""
        generator = BehaviorGenerator(user_pool_size=100, seed=42)
        event = generator.generate()

        assert event is not None
        assert event.user_id.startswith("user_")
        assert event.event_type in EventType
        assert event.event_id is not None
        assert event.timestamp is not None

    def test_generate_batch(self):
        """测试批量生成事件"""
        generator = BehaviorGenerator(user_pool_size=100)
        events = generator.generate_batch(100)

        assert len(events) == 100
        for event in events:
            assert event.user_id.startswith("user_")
            assert event.event_type in EventType

    def test_generate_view_event_properties(self):
        """测试 VIEW 事件属性"""
        generator = BehaviorGenerator(user_pool_size=100)
        # 多次生成直到得到 VIEW 事件
        for _ in range(100):
            event = generator.generate()
            if event.event_type == EventType.VIEW:
                assert "stay_duration" in event.properties
                assert "scroll_depth" in event.properties
                break

    def test_generate_purchase_event_properties(self):
        """测试 PURCHASE 事件属性"""
        generator = BehaviorGenerator(user_pool_size=100)
        # 多次生成直到得到 PURCHASE 事件
        for _ in range(100):
            event = generator.generate()
            if event.event_type == EventType.PURCHASE:
                assert "amount" in event.properties
                assert "product_id" in event.properties
                assert "quantity" in event.properties
                break

    def test_generate_search_event_properties(self):
        """测试 SEARCH 事件属性"""
        generator = BehaviorGenerator(user_pool_size=100)
        # 多次生成直到得到 SEARCH 事件
        for _ in range(100):
            event = generator.generate()
            if event.event_type == EventType.SEARCH:
                assert "keyword" in event.properties
                assert "result_count" in event.properties
                break

    def test_user_id_in_range(self):
        """测试用户ID在范围内"""
        generator = BehaviorGenerator(user_pool_size=100)
        events = generator.generate_batch(1000)

        for event in events:
            user_num = int(event.user_id.split("_")[1])
            assert 1 <= user_num <= 100


class TestWeightedBehaviorGenerator:
    """带权重的行为生成器测试"""

    def test_create_weighted_generator(self):
        """测试创建带权重的生成器"""
        generator = WeightedBehaviorGenerator(user_pool_size=100)
        assert generator.event_weights is not None
        assert len(generator.event_weights) == len(EventType)

    def test_custom_weights(self):
        """测试自定义权重"""
        custom_weights = {
            EventType.VIEW: 0.5,
            EventType.CLICK: 0.3,
            EventType.PURCHASE: 0.2,
        }
        generator = WeightedBehaviorGenerator(
            user_pool_size=100,
            event_weights=custom_weights
        )
        assert generator.event_weights == custom_weights

    def test_weighted_distribution(self):
        """测试权重分布"""
        generator = WeightedBehaviorGenerator(
            user_pool_size=100,
            seed=42
        )
        events = generator.generate_batch(1000)

        # 统计各事件类型数量
        type_counts = {}
        for event in events:
            event_type = event.event_type
            type_counts[event_type] = type_counts.get(event_type, 0) + 1

        # VIEW 应该是最多的（权重 0.40）
        assert type_counts.get(EventType.VIEW, 0) > type_counts.get(EventType.PURCHASE, 0)

    def test_weighted_generator_with_seed(self):
        """测试带种子的权重生成器"""
        generator1 = WeightedBehaviorGenerator(user_pool_size=100, seed=42)
        generator2 = WeightedBehaviorGenerator(user_pool_size=100, seed=42)

        events1 = generator1.generate_batch(10)
        events2 = generator2.generate_batch(10)

        for e1, e2 in zip(events1, events2):
            assert e1.user_id == e2.user_id
            assert e1.event_type == e2.event_type


class TestBehaviorGeneratorAsync:
    """行为生成器异步测试"""

    @pytest.mark.asyncio
    async def test_stream_generate(self):
        """测试流式生成"""
        generator = BehaviorGenerator(user_pool_size=100, seed=42)
        events = []

        async for event in generator.stream(rate_per_second=100, count=10):
            events.append(event)

        assert len(events) == 10

    @pytest.mark.asyncio
    async def test_stream_rate_limit(self):
        """测试流式生成速率限制"""
        import time

        generator = BehaviorGenerator(user_pool_size=100)
        count = 5
        rate = 10  # 每秒 10 个

        start_time = time.time()
        events = []
        async for event in generator.stream(rate_per_second=rate, count=count):
            events.append(event)
        elapsed = time.time() - start_time

        # 5 个事件，每秒 10 个，应该耗时约 0.4-0.6 秒
        assert len(events) == count
        assert 0.3 < elapsed < 1.0
