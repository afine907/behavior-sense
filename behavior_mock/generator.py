"""
用户行为生成器

生成模拟用户行为数据，支持多种事件类型和场景。
"""
import random
import asyncio
from datetime import datetime
from typing import AsyncIterator
from behavior_core.models.event import UserBehavior, EventType
from behavior_core.utils.logging import get_logger

logger = get_logger(__name__)


class BehaviorGenerator:
    """用户行为生成器"""

    def __init__(
        self,
        user_pool_size: int = 1000,
        event_types: list[EventType] | None = None,
        seed: int | None = None,
    ):
        """
        初始化行为生成器

        Args:
            user_pool_size: 用户池大小
            event_types: 支持的事件类型列表，None 表示支持所有类型
            seed: 随机种子，用于可复现的生成
        """
        self.user_pool_size = user_pool_size
        self.event_types = event_types or list(EventType)
        self._seed = seed

        if seed is not None:
            random.seed(seed)

        # 模拟页面列表
        self._pages = [
            "/home",
            "/product/123",
            "/product/456",
            "/product/789",
            "/cart",
            "/checkout",
            "/profile",
            "/search",
            "/category/electronics",
            "/category/clothing",
            "/category/books",
        ]

        # 模拟搜索关键词
        self._keywords = [
            "手机", "笔记本", "耳机", "键盘", "鼠标",
            "衣服", "鞋子", "包", "手表", "眼镜",
            "book", "programming", "python", "data science",
        ]

        # 模拟商品
        self._products = [f"prod_{i}" for i in range(1, 501)]

        logger.info(
            "behavior_generator_initialized",
            user_pool_size=user_pool_size,
            event_types=[e.value for e in self.event_types],
        )

    def generate(self) -> UserBehavior:
        """
        生成单条用户行为

        Returns:
            UserBehavior: 生成的用户行为事件
        """
        user_id = f"user_{random.randint(1, self.user_pool_size)}"
        event_type = random.choice(self.event_types)
        session_id = f"session_{random.randint(1, 100)}"
        page_url = random.choice(self._pages) if random.random() > 0.3 else None

        properties = self._generate_properties(event_type)

        event = UserBehavior(
            user_id=user_id,
            event_type=event_type,
            session_id=session_id,
            page_url=page_url,
            properties=properties,
        )

        logger.debug(
            "event_generated",
            event_id=event.event_id,
            user_id=user_id,
            event_type=event_type.value,
        )

        return event

    def _generate_properties(self, event_type: EventType) -> dict:
        """
        根据事件类型生成属性

        Args:
            event_type: 事件类型

        Returns:
            生成的属性字典
        """
        properties = {}

        if event_type == EventType.VIEW:
            properties["page_url"] = random.choice(self._pages)
            properties["stay_duration"] = random.randint(5, 300)
            properties["scroll_depth"] = round(random.uniform(0, 1), 2)

        elif event_type == EventType.CLICK:
            properties["element_id"] = f"btn_{random.randint(1, 50)}"
            properties["element_type"] = random.choice(["button", "link", "image", "banner"])
            properties["x"] = random.randint(0, 1920)
            properties["y"] = random.randint(0, 1080)

        elif event_type == EventType.SEARCH:
            properties["keyword"] = random.choice(self._keywords)
            properties["result_count"] = random.randint(0, 100)
            properties["page_number"] = random.randint(1, 10)
            properties["filters"] = random.choice([{}, {"price_min": 100}, {"brand": "test"}])

        elif event_type == EventType.PURCHASE:
            properties["product_id"] = random.choice(self._products)
            properties["amount"] = round(random.uniform(10, 5000), 2)
            properties["quantity"] = random.randint(1, 5)
            properties["payment_method"] = random.choice(["alipay", "wechat", "credit_card"])

        elif event_type == EventType.COMMENT:
            properties["product_id"] = random.choice(self._products)
            properties["rating"] = random.randint(1, 5)
            properties["content_length"] = random.randint(10, 200)
            properties["has_image"] = random.random() > 0.7

        elif event_type == EventType.LOGIN:
            properties["login_method"] = random.choice(["password", "sms", "wechat", "qq"])
            properties["device_type"] = random.choice(["mobile", "desktop", "tablet"])
            properties["success"] = random.random() > 0.1  # 90% 成功率

        elif event_type == EventType.LOGOUT:
            properties["session_duration"] = random.randint(60, 7200)

        elif event_type == EventType.REGISTER:
            properties["register_method"] = random.choice(["email", "phone", "third_party"])
            properties["invite_code"] = random.choice([None, f"INV{random.randint(1000, 9999)}"])

        elif event_type == EventType.FAVORITE:
            properties["product_id"] = random.choice(self._products)
            properties["action"] = random.choice(["add", "remove"])

        elif event_type == EventType.SHARE:
            properties["product_id"] = random.choice(self._products)
            properties["platform"] = random.choice(["wechat", "weibo", "qq", "link"])
            properties["content_type"] = random.choice(["product", "activity", "article"])

        return properties

    def generate_batch(self, count: int) -> list[UserBehavior]:
        """
        批量生成用户行为

        Args:
            count: 生成数量

        Returns:
            用户行为列表
        """
        events = [self.generate() for _ in range(count)]
        logger.info("batch_generated", count=count)
        return events

    async def stream(
        self,
        rate_per_second: int = 100,
        count: int | None = None,
    ) -> AsyncIterator[UserBehavior]:
        """
        流式生成用户行为

        Args:
            rate_per_second: 每秒生成速率
            count: 总生成数量，None 表示无限生成

        Yields:
            UserBehavior: 生成的用户行为事件
        """
        interval = 1.0 / rate_per_second
        generated = 0

        logger.info(
            "stream_started",
            rate_per_second=rate_per_second,
            max_count=count,
        )

        try:
            while count is None or generated < count:
                yield self.generate()
                generated += 1
                await asyncio.sleep(interval)
        finally:
            logger.info("stream_stopped", generated_count=generated)


class WeightedBehaviorGenerator(BehaviorGenerator):
    """带权重的行为生成器"""

    def __init__(
        self,
        user_pool_size: int = 1000,
        event_weights: dict[EventType, float] | None = None,
        seed: int | None = None,
    ):
        """
        初始化带权重的行为生成器

        Args:
            user_pool_size: 用户池大小
            event_weights: 事件类型权重映射，None 表示均匀分布
            seed: 随机种子
        """
        super().__init__(user_pool_size=user_pool_size, seed=seed)

        # 默认权重：浏览 > 点击 > 搜索 > 其他
        default_weights = {
            EventType.VIEW: 0.40,
            EventType.CLICK: 0.25,
            EventType.SEARCH: 0.15,
            EventType.PURCHASE: 0.05,
            EventType.COMMENT: 0.03,
            EventType.LOGIN: 0.05,
            EventType.LOGOUT: 0.03,
            EventType.REGISTER: 0.01,
            EventType.FAVORITE: 0.02,
            EventType.SHARE: 0.01,
        }

        self.event_weights = event_weights or default_weights
        self._weighted_events = list(self.event_weights.keys())
        self._weights = list(self.event_weights.values())

        logger.info(
            "weighted_generator_initialized",
            weights={e.value: w for e, w in self.event_weights.items()},
        )

    def generate(self) -> UserBehavior:
        """生成带权重的用户行为"""
        user_id = f"user_{random.randint(1, self.user_pool_size)}"
        event_type = random.choices(
            self._weighted_events,
            weights=self._weights,
            k=1,
        )[0]
        session_id = f"session_{random.randint(1, 100)}"
        page_url = random.choice(self._pages) if random.random() > 0.3 else None

        properties = self._generate_properties(event_type)

        return UserBehavior(
            user_id=user_id,
            event_type=event_type,
            session_id=session_id,
            page_url=page_url,
            properties=properties,
        )
