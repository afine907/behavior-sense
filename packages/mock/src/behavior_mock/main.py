"""
FastAPI 应用入口

提供 REST API 用于控制用户行为模拟器。
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from behavior_core.config.settings import get_settings
from behavior_core.models.event import EventType
from behavior_core.utils.logging import get_logger, setup_logging
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from behavior_mock.generator import BehaviorGenerator, WeightedBehaviorGenerator
from behavior_mock.producer import MockProducer, PulsarProducer
from behavior_mock.scenarios import (
    Scenario,
    ScenarioStatus,
    create_scenario,
)

settings = get_settings()
logger = get_logger(__name__)

# 全局状态
_scenario_registry: dict[str, Scenario] = {}
_producer: PulsarProducer | MockProducer | None = None


# 请求/响应模型
class GenerateRequest(BaseModel):
    """生成事件请求"""
    count: int = Field(default=1, ge=1, le=10000, description="生成数量")
    user_pool_size: int = Field(default=1000, ge=1, description="用户池大小")
    event_types: list[str] | None = Field(default=None, description="事件类型列表")
    seed: int | None = Field(default=None, description="随机种子")
    weighted: bool = Field(default=True, description="是否使用权重生成")


class GenerateResponse(BaseModel):
    """生成事件响应"""
    events: list[dict]
    count: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ScenarioStartRequest(BaseModel):
    """启动场景请求"""
    scenario_type: str = Field(description="场景类型")
    scenario_id: str | None = Field(default=None, description="场景ID")
    duration_seconds: int | None = Field(default=None, description="持续时间")
    rate_per_second: int | None = Field(default=None, description="每秒事件数")
    # 秒杀场景参数
    peak_rate: int | None = Field(default=None, description="峰值速率")
    product_id: str | None = Field(default=None, description="商品ID")
    # 异常流量参数
    attack_type: str | None = Field(default=None, description="攻击类型")
    malicious_user_ratio: float | None = Field(default=None, description="恶意用户比例")
    # 渐进负载参数
    start_rate: int | None = Field(default=None, description="起始速率")
    end_rate: int | None = Field(default=None, description="结束速率")


class ScenarioInfo(BaseModel):
    """场景信息"""
    scenario_id: str
    name: str
    status: str
    duration_seconds: float | None
    elapsed_seconds: float | None
    start_time: str | None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: datetime
    active_scenarios: int
    producer_connected: bool


def get_producer() -> PulsarProducer | MockProducer:
    """获取生产者实例"""
    global _producer
    if _producer is None:
        # 在开发环境使用 MockProducer
        if settings.app_env == "development":
            _producer = MockProducer()
        else:
            _producer = PulsarProducer()
        _producer.connect()
    return _producer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    setup_logging()
    logger.info("behavior_mock_service_starting", port=settings.mock_port)

    # 初始化生产者
    global _producer
    if settings.app_env == "development":
        _producer = MockProducer()
    else:
        _producer = PulsarProducer()
    _producer.connect()

    yield

    # 关闭时
    logger.info("behavior_mock_service_stopping")
    if _producer:
        _producer.close()

    # 停止所有运行中的场景
    for scenario in _scenario_registry.values():
        if scenario.status == ScenarioStatus.RUNNING:
            scenario.stop()


app = FastAPI(
    title="BehaviorSense Mock Service",
    description="用户行为模拟器服务",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """健康检查"""
    active_count = sum(
        1 for s in _scenario_registry.values()
        if s.status == ScenarioStatus.RUNNING
    )

    producer_connected = (
        isinstance(_producer, MockProducer) or _producer._producer is not None
    ) if _producer else False

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        active_scenarios=active_count,
        producer_connected=producer_connected,
    )


@app.post("/api/mock/generate", response_model=GenerateResponse, tags=["Generator"])
async def generate_events(request: GenerateRequest):
    """
    生成用户行为事件

    支持批量生成和权重生成。
    """
    # 解析事件类型
    event_types = None
    if request.event_types:
        try:
            event_types = [EventType(et) for et in request.event_types]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {e}")

    # 创建生成器
    if request.weighted:
        generator = WeightedBehaviorGenerator(
            user_pool_size=request.user_pool_size,
            seed=request.seed,
        )
    else:
        generator = BehaviorGenerator(
            user_pool_size=request.user_pool_size,
            event_types=event_types,
            seed=request.seed,
        )

    # 生成事件
    events = generator.generate_batch(request.count)

    logger.info("events_generated", count=request.count, weighted=request.weighted)

    return GenerateResponse(
        events=[e.model_dump() for e in events],
        count=len(events),
    )


@app.post("/api/mock/generate_and_send", tags=["Generator"])
async def generate_and_send_events(request: GenerateRequest):
    """
    生成并发送用户行为事件到 Pulsar
    """
    producer = get_producer()

    # 解析事件类型
    event_types = None
    if request.event_types:
        try:
            event_types = [EventType(et) for et in request.event_types]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {e}")

    # 创建生成器
    if request.weighted:
        generator = WeightedBehaviorGenerator(
            user_pool_size=request.user_pool_size,
            seed=request.seed,
        )
    else:
        generator = BehaviorGenerator(
            user_pool_size=request.user_pool_size,
            event_types=event_types,
            seed=request.seed,
        )

    # 生成事件
    events = generator.generate_batch(request.count)

    # 发送事件
    try:
        if isinstance(producer, MockProducer):
            for event in events:
                producer.send(event)
            sent_count = request.count
        else:
            message_ids = await producer.send_batch_async(events)
            sent_count = len(message_ids)

        logger.info("events_sent", count=sent_count)

        return {
            "status": "ok",
            "generated": len(events),
            "sent": sent_count,
        }
    except Exception as e:
        logger.error("send_events_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mock/scenario/start", response_model=ScenarioInfo, tags=["Scenario"])
async def start_scenario(
    request: ScenarioStartRequest,
    background_tasks: BackgroundTasks,
):
    """
    启动模拟场景

    支持的场景类型：
    - normal: 正常流量
    - flash_sale: 秒杀活动
    - abnormal: 异常流量
    - gradual: 渐进负载
    """
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    scenario_id = request.scenario_id or f"{request.scenario_type}-{timestamp}"

    # 检查是否已存在
    if scenario_id in _scenario_registry:
        existing = _scenario_registry[scenario_id]
        if existing.status == ScenarioStatus.RUNNING:
            raise HTTPException(
                status_code=400,
                detail=f"Scenario {scenario_id} is already running",
            )

    # 构建场景参数
    kwargs: dict = {}

    if request.duration_seconds is not None:
        kwargs["duration_seconds"] = request.duration_seconds

    if request.scenario_type == "normal" and request.rate_per_second:
        kwargs["rate_per_second"] = request.rate_per_second

    if request.scenario_type == "flash_sale":
        if request.peak_rate:
            kwargs["peak_rate"] = request.peak_rate
        if request.product_id:
            kwargs["product_id"] = request.product_id

    if request.scenario_type == "abnormal":
        if request.attack_type:
            kwargs["attack_type"] = request.attack_type
        if request.malicious_user_ratio:
            kwargs["malicious_user_ratio"] = request.malicious_user_ratio
        if request.rate_per_second:
            kwargs["rate_per_second"] = request.rate_per_second

    if request.scenario_type == "gradual":
        if request.start_rate:
            kwargs["start_rate"] = request.start_rate
        if request.end_rate:
            kwargs["end_rate"] = request.end_rate

    # 创建场景
    try:
        scenario = create_scenario(
            request.scenario_type,
            scenario_id=scenario_id,
            **kwargs,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 注册场景
    _scenario_registry[scenario_id] = scenario

    # 后台运行场景
    async def run_scenario():
        producer = get_producer()
        try:
            async for event in scenario.stream():
                if isinstance(producer, MockProducer):
                    producer.send(event)
                else:
                    await producer.send_async(event)
        except asyncio.CancelledError:
            logger.info("scenario_cancelled", scenario_id=scenario_id)
        except Exception as e:
            logger.error("scenario_error", scenario_id=scenario_id, error=str(e))
            scenario._status = ScenarioStatus.ERROR

    background_tasks.add_task(run_scenario)

    logger.info(
        "scenario_started",
        scenario_id=scenario_id,
        type=request.scenario_type,
    )

    return ScenarioInfo(
        scenario_id=scenario.scenario_id,
        name=scenario.name,
        status=scenario.status.value,
        duration_seconds=scenario.duration_seconds,
        elapsed_seconds=scenario.elapsed_seconds,
        start_time=scenario._start_time.isoformat() if scenario._start_time else None,
    )


@app.post("/api/mock/scenario/{scenario_id}/stop", tags=["Scenario"])
async def stop_scenario(scenario_id: str):
    """停止场景"""
    if scenario_id not in _scenario_registry:
        raise HTTPException(status_code=404, detail="Scenario not found")

    scenario = _scenario_registry[scenario_id]
    scenario.stop()

    logger.info("scenario_stopped", scenario_id=scenario_id)

    return {
        "status": "ok",
        "scenario_id": scenario_id,
        "final_status": scenario.status.value,
    }


@app.post("/api/mock/scenario/{scenario_id}/pause", tags=["Scenario"])
async def pause_scenario(scenario_id: str):
    """暂停场景"""
    if scenario_id not in _scenario_registry:
        raise HTTPException(status_code=404, detail="Scenario not found")

    scenario = _scenario_registry[scenario_id]
    scenario.pause()

    return {"status": "ok", "scenario_id": scenario_id}


@app.post("/api/mock/scenario/{scenario_id}/resume", tags=["Scenario"])
async def resume_scenario(scenario_id: str):
    """恢复场景"""
    if scenario_id not in _scenario_registry:
        raise HTTPException(status_code=404, detail="Scenario not found")

    scenario = _scenario_registry[scenario_id]
    scenario.resume()

    return {"status": "ok", "scenario_id": scenario_id}


@app.get("/api/mock/scenario/{scenario_id}", response_model=ScenarioInfo, tags=["Scenario"])
async def get_scenario_info(scenario_id: str):
    """获取场景信息"""
    if scenario_id not in _scenario_registry:
        raise HTTPException(status_code=404, detail="Scenario not found")

    scenario = _scenario_registry[scenario_id]

    return ScenarioInfo(
        scenario_id=scenario.scenario_id,
        name=scenario.name,
        status=scenario.status.value,
        duration_seconds=scenario.duration_seconds,
        elapsed_seconds=scenario.elapsed_seconds,
        start_time=scenario._start_time.isoformat() if scenario._start_time else None,
    )


@app.get("/api/mock/scenarios", response_model=list[ScenarioInfo], tags=["Scenario"])
async def list_scenarios(
    status: ScenarioStatus | None = None,
):
    """列出所有场景"""
    scenarios = list(_scenario_registry.values())

    if status:
        scenarios = [s for s in scenarios if s.status == status]

    return [
        ScenarioInfo(
            scenario_id=s.scenario_id,
            name=s.name,
            status=s.status.value,
            duration_seconds=s.duration_seconds,
            elapsed_seconds=s.elapsed_seconds,
            start_time=s._start_time.isoformat() if s._start_time else None,
        )
        for s in scenarios
    ]


@app.delete("/api/mock/scenario/{scenario_id}", tags=["Scenario"])
async def delete_scenario(scenario_id: str):
    """删除场景"""
    if scenario_id not in _scenario_registry:
        raise HTTPException(status_code=404, detail="Scenario not found")

    scenario = _scenario_registry[scenario_id]

    if scenario.status == ScenarioStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a running scenario. Stop it first.",
        )

    del _scenario_registry[scenario_id]

    logger.info("scenario_deleted", scenario_id=scenario_id)

    return {"status": "ok", "scenario_id": scenario_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "behavior_mock.main:app",
        host="0.0.0.0",
        port=settings.mock_port,
        reload=settings.debug,
    )
