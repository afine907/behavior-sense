"""
模拟场景定义

定义各种模拟场景，如秒杀活动、异常流量等。
"""
import asyncio
import random
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from enum import Enum

from behavior_core.models.event import EventType, UserBehavior
from behavior_core.utils.logging import get_logger

from behavior_mock.generator import BehaviorGenerator, WeightedBehaviorGenerator

logger = get_logger(__name__)


class ScenarioStatus(str, Enum):
    """场景状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"


class Scenario(ABC):
    """场景基类"""

    def __init__(
        self,
        scenario_id: str,
        name: str,
        duration_seconds: int | None = None,
    ):
        """
        初始化场景

        Args:
            scenario_id: 场景ID
            name: 场景名称
            duration_seconds: 场景持续时间(秒)，None 表示无限
        """
        self.scenario_id = scenario_id
        self.name = name
        self.duration_seconds = duration_seconds
        self._status = ScenarioStatus.IDLE
        self._start_time: datetime | None = None
        self._stop_event = asyncio.Event()

        logger.info(
            "scenario_created",
            scenario_id=scenario_id,
            name=name,
            duration=duration_seconds,
        )

    @property
    def status(self) -> ScenarioStatus:
        """获取场景状态"""
        return self._status

    @property
    def elapsed_seconds(self) -> float | None:
        """获取已运行时间(秒)"""
        if self._start_time is None:
            return None
        return (datetime.now(timezone.utc) - self._start_time).total_seconds()

    @abstractmethod
    async def stream(self) -> AsyncIterator[UserBehavior]:
        """
        流式生成事件

        Yields:
            UserBehavior: 用户行为事件
        """
        pass

    def start(self) -> None:
        """启动场景"""
        if self._status == ScenarioStatus.RUNNING:
            logger.warning("scenario_already_running", scenario_id=self.scenario_id)
            return

        self._status = ScenarioStatus.RUNNING
        # 只在第一次启动时设置开始时间
        if self._start_time is None:
            self._start_time = datetime.now(timezone.utc)
        self._stop_event.clear()
        logger.info("scenario_started", scenario_id=self.scenario_id)

    def stop(self) -> None:
        """停止场景"""
        self._status = ScenarioStatus.STOPPED
        self._stop_event.set()
        logger.info("scenario_stopped", scenario_id=self.scenario_id)

    def pause(self) -> None:
        """暂停场景"""
        if self._status == ScenarioStatus.RUNNING:
            self._status = ScenarioStatus.PAUSED
            logger.info("scenario_paused", scenario_id=self.scenario_id)

    def resume(self) -> None:
        """恢复场景"""
        if self._status == ScenarioStatus.PAUSED:
            self._status = ScenarioStatus.RUNNING
            logger.info("scenario_resumed", scenario_id=self.scenario_id)

    def _should_continue(self) -> bool:
        """检查是否应该继续生成"""
        if self._stop_event.is_set():
            return False
        if self._status != ScenarioStatus.RUNNING:
            return False
        if self.duration_seconds and self.elapsed_seconds:
            if self.elapsed_seconds >= self.duration_seconds:
                self._status = ScenarioStatus.COMPLETED
                return False
        return True

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "status": self._status.value,
            "duration_seconds": self.duration_seconds,
            "elapsed_seconds": self.elapsed_seconds,
            "start_time": self._start_time.isoformat() if self._start_time else None,
        }


class NormalScenario(Scenario):
    """正常流量场景"""

    def __init__(
        self,
        scenario_id: str = "normal-001",
        rate_per_second: int = 100,
        duration_seconds: int | None = None,
        user_pool_size: int = 1000,
    ):
        """
        初始化正常场景

        Args:
            scenario_id: 场景ID
            rate_per_second: 每秒事件数
            duration_seconds: 持续时间
            user_pool_size: 用户池大小
        """
        super().__init__(scenario_id, "Normal Traffic", duration_seconds)
        self.rate_per_second = rate_per_second
        self.generator = WeightedBehaviorGenerator(user_pool_size=user_pool_size)

    async def stream(self) -> AsyncIterator[UserBehavior]:
        """流式生成事件"""
        interval = 1.0 / self.rate_per_second
        # 注意：start() 应该在调用 stream() 之前被调用
        # 如果状态不是 RUNNING，尝试启动
        if self._status != ScenarioStatus.RUNNING:
            self.start()

        try:
            while self._should_continue():
                yield self.generator.generate()
                await asyncio.sleep(interval)
        finally:
            # 只有在仍在运行状态时才标记为完成
            # 这允许外部控制停止场景而不自动变为完成
            pass


class FlashSaleScenario(Scenario):
    """秒杀场景 - 模拟高并发购买"""

    def __init__(
        self,
        scenario_id: str = "flash-sale-001",
        peak_rate: int = 5000,
        duration_seconds: int = 300,
        product_id: str = "flash-product-001",
        user_pool_size: int = 10000,
    ):
        """
        初始化秒杀场景

        Args:
            scenario_id: 场景ID
            peak_rate: 峰值每秒事件数
            duration_seconds: 持续时间
            product_id: 秒杀商品ID
            user_pool_size: 用户池大小
        """
        super().__init__(scenario_id, "Flash Sale", duration_seconds)
        self.peak_rate = peak_rate
        self.product_id = product_id
        self.generator = BehaviorGenerator(
            user_pool_size=user_pool_size,
            event_types=[EventType.VIEW, EventType.CLICK, EventType.PURCHASE],
        )

    def _get_current_rate(self) -> int:
        """
        计算当前速率(模拟流量曲线)

        流量曲线：缓慢上升 -> 急剧峰值 -> 快速下降 -> 平稳
        """
        elapsed = self.elapsed_seconds or 0
        total = self.duration_seconds or 300

        # 归一化时间 [0, 1]
        t = elapsed / total

        # 使用分段函数模拟流量曲线
        if t < 0.2:
            # 上升阶段
            ratio = t / 0.2
            return int(self.peak_rate * ratio)
        elif t < 0.3:
            # 峰值阶段
            return self.peak_rate
        elif t < 0.5:
            # 快速下降
            ratio = 1 - (t - 0.3) / 0.2
            return int(self.peak_rate * (0.3 + 0.7 * ratio))
        else:
            # 平稳阶段
            return int(self.peak_rate * 0.1)

    async def stream(self) -> AsyncIterator[UserBehavior]:
        """流式生成事件"""
        if self._status != ScenarioStatus.RUNNING:
            self.start()

        try:
            while self._should_continue():
                current_rate = self._get_current_rate()
                interval = 1.0 / max(current_rate, 1)

                event = self.generator.generate()
                # 添加秒杀商品相关属性
                if event.event_type == EventType.PURCHASE:
                    event.properties["product_id"] = self.product_id
                    event.properties["flash_sale"] = True

                yield event
                await asyncio.sleep(interval)
        finally:
            pass


class AbnormalTrafficScenario(Scenario):
    """异常流量场景 - 模拟爬虫或攻击"""

    def __init__(
        self,
        scenario_id: str = "abnormal-001",
        rate_per_second: int = 1000,
        duration_seconds: int = 60,
        attack_type: str = "crawling",
        malicious_user_ratio: float = 0.3,
    ):
        """
        初始化异常流量场景

        Args:
            scenario_id: 场景ID
            rate_per_second: 每秒事件数
            duration_seconds: 持续时间
            attack_type: 攻击类型 (crawling, brute_force, spam)
            malicious_user_ratio: 恶意用户比例
        """
        super().__init__(scenario_id, "Abnormal Traffic", duration_seconds)
        self.rate_per_second = rate_per_second
        self.attack_type = attack_type
        self.malicious_user_ratio = malicious_user_ratio

        # 正常用户生成器
        self.normal_generator = WeightedBehaviorGenerator(user_pool_size=1000)

        # 恶意用户生成器
        self.malicious_generator = self._create_malicious_generator()

        logger.info(
            "abnormal_scenario_initialized",
            attack_type=attack_type,
            malicious_ratio=malicious_user_ratio,
        )

    def _create_malicious_generator(self) -> BehaviorGenerator:
        """创建恶意用户生成器"""
        if self.attack_type == "crawling":
            # 爬虫：高频浏览
            return BehaviorGenerator(
                user_pool_size=10,
                event_types=[EventType.VIEW],
                seed=42,
            )
        elif self.attack_type == "brute_force":
            # 暴力破解：高频登录尝试
            return BehaviorGenerator(
                user_pool_size=5,
                event_types=[EventType.LOGIN],
                seed=42,
            )
        elif self.attack_type == "spam":
            # 垃圾信息：高频评论
            return BehaviorGenerator(
                user_pool_size=20,
                event_types=[EventType.COMMENT],
                seed=42,
            )
        else:
            return BehaviorGenerator(user_pool_size=10, seed=42)

    def _generate_malicious_properties(self, event: UserBehavior) -> UserBehavior:
        """生成恶意行为特征"""
        if self.attack_type == "crawling":
            event.properties["stay_duration"] = 0  # 无停留
            event.properties["scroll_depth"] = 0
            event.user_agent = "Bot/1.0"

        elif self.attack_type == "brute_force":
            event.properties["success"] = False  # 登录失败
            event.properties["attempts"] = random.randint(10, 100)

        elif self.attack_type == "spam":
            event.properties["rating"] = 1  # 低评分
            event.properties["has_image"] = False

        return event

    async def stream(self) -> AsyncIterator[UserBehavior]:
        """流式生成事件"""
        interval = 1.0 / self.rate_per_second
        if self._status != ScenarioStatus.RUNNING:
            self.start()

        try:
            while self._should_continue():
                # 决定是正常用户还是恶意用户
                if random.random() < self.malicious_user_ratio:
                    event = self.malicious_generator.generate()
                    event = self._generate_malicious_properties(event)
                    event.properties["is_malicious"] = True
                else:
                    event = self.normal_generator.generate()
                    event.properties["is_malicious"] = False

                yield event
                await asyncio.sleep(interval)
        finally:
            pass


class GradualLoadScenario(Scenario):
    """渐进负载场景 - 用于压测"""

    def __init__(
        self,
        scenario_id: str = "gradual-001",
        start_rate: int = 10,
        end_rate: int = 1000,
        duration_seconds: int = 600,
        user_pool_size: int = 5000,
    ):
        """
        初始化渐进负载场景

        Args:
            scenario_id: 场景ID
            start_rate: 起始速率
            end_rate: 结束速率
            duration_seconds: 持续时间
            user_pool_size: 用户池大小
        """
        super().__init__(scenario_id, "Gradual Load", duration_seconds)
        self.start_rate = start_rate
        self.end_rate = end_rate
        self.generator = WeightedBehaviorGenerator(user_pool_size=user_pool_size)

    def _get_current_rate(self) -> int:
        """计算当前速率"""
        elapsed = self.elapsed_seconds or 0
        total = self.duration_seconds or 600

        # 线性增长
        ratio = elapsed / total
        return int(self.start_rate + (self.end_rate - self.start_rate) * ratio)

    async def stream(self) -> AsyncIterator[UserBehavior]:
        """流式生成事件"""
        if self._status != ScenarioStatus.RUNNING:
            self.start()

        try:
            while self._should_continue():
                current_rate = self._get_current_rate()
                interval = 1.0 / max(current_rate, 1)

                yield self.generator.generate()
                await asyncio.sleep(interval)
        finally:
            pass


# 场景工厂
SCENARIO_REGISTRY: dict[str, type[Scenario]] = {
    "normal": NormalScenario,
    "flash_sale": FlashSaleScenario,
    "abnormal": AbnormalTrafficScenario,
    "gradual": GradualLoadScenario,
}


def create_scenario(
    scenario_type: str,
    scenario_id: str,
    **kwargs,
) -> Scenario:
    """
    创建场景实例

    Args:
        scenario_type: 场景类型
        scenario_id: 场景ID
        **kwargs: 场景参数

    Returns:
        Scenario: 场景实例
    """
    scenario_class = SCENARIO_REGISTRY.get(scenario_type)
    if scenario_class is None:
        raise ValueError(f"Unknown scenario type: {scenario_type}")

    return scenario_class(scenario_id=scenario_id, **kwargs)
