"""
用户行为模拟器模块

用于生成模拟用户行为数据，支持多种事件类型和场景。
"""
from behavior_mock.generator import BehaviorGenerator, WeightedBehaviorGenerator
from behavior_mock.producer import PulsarProducer, MockProducer
from behavior_mock.scenarios import (
    Scenario,
    ScenarioStatus,
    NormalScenario,
    FlashSaleScenario,
    AbnormalTrafficScenario,
    GradualLoadScenario,
    create_scenario,
    SCENARIO_REGISTRY,
)

__all__ = [
    # 生成器
    "BehaviorGenerator",
    "WeightedBehaviorGenerator",
    # 生产者
    "PulsarProducer",
    "MockProducer",
    # 场景
    "Scenario",
    "ScenarioStatus",
    "NormalScenario",
    "FlashSaleScenario",
    "AbnormalTrafficScenario",
    "GradualLoadScenario",
    "create_scenario",
    "SCENARIO_REGISTRY",
]
