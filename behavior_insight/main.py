"""
BehaviorSense Insight 服务
洞察分析服务 - 标签管理、用户画像、分析报表
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from behavior_core.config.settings import get_settings
from behavior_core.utils.logging import setup_logging, get_logger
from behavior_core.middleware.tracing import TraceIDMiddleware
from behavior_core.middleware.rate_limit import RateLimitMiddleware
from behavior_core.metrics import get_metrics, set_service_info, increment_request_counter
from behavior_insight.services.tag_service import TagService
from behavior_insight.repositories.user_repo import UserRepository, init_database
from behavior_insight.routers import tags, profile

settings = get_settings()
logger = get_logger(__name__)


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    redis: str
    database: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 设置日志
    setup_logging()
    logger.info("Starting Insight service", port=settings.insight_port)

    # 初始化 Redis
    redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=settings.redis_max_connections,
    )

    # 初始化数据库
    async_session_factory = await init_database(settings.database_url)

    # 创建服务实例
    app.state.redis = redis_client
    app.state.async_session_factory = async_session_factory
    app.state.tag_service = TagService(redis_client)

    # 创建一个默认的 session 用于 user_repo
    async with async_session_factory() as session:
        app.state.user_repo = UserRepository(session)
        app.state.db_session = session

        yield

    # 清理资源
    await redis_client.close()
    logger.info("Insight service stopped")


# 创建 FastAPI 应用
app = FastAPI(
    title="BehaviorSense Insight",
    description="洞察分析服务 - 标签管理、用户画像、分析报表",
    version="1.0.0",
    lifespan=lifespan,
)

# 设置服务信息
set_service_info("behavior-insight", "1.0.0")

# 添加 TraceID 中间件
app.add_middleware(TraceIDMiddleware)

# 添加限流中间件
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=100,
    window_seconds=60,
)

# 配置 CORS (从配置读取允许的域名)
cors_origins = settings.cors_origins.split(",") if settings.cors_origins else ["*"] if settings.debug else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求中间件 - 为每个请求创建新的数据库会话
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    """为每个请求创建独立的数据库会话"""
    async_session_factory = request.app.state.async_session_factory

    async with async_session_factory() as session:
        request.state.db_session = session
        request.state.user_repo = UserRepository(session)
        response = await call_next(request)

    return response


# 异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.exception(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# 注册路由
app.include_router(tags.router)
app.include_router(profile.router)


@app.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """
    健康检查

    检查服务和依赖项的状态
    """
    # 检查 Redis
    redis_status = "ok"
    try:
        redis_client: redis.Redis = request.app.state.redis
        await redis_client.ping()
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        redis_status = "error"

    # 检查数据库
    db_status = "ok"
    try:
        session: AsyncSession = request.state.db_session
        await session.execute("SELECT 1")
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        db_status = "error"

    return HealthResponse(
        status="ok" if redis_status == "ok" and db_status == "ok" else "degraded",
        service="insight",
        redis=redis_status,
        database=db_status,
    )


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics_endpoint() -> str:
    """
    Prometheus 指标端点

    返回 Prometheus 格式的监控指标
    """
    return get_metrics()


@app.get("/")
async def root() -> dict[str, str]:
    """服务根路径"""
    return {
        "service": "BehaviorSense Insight",
        "version": "1.0.0",
        "docs": "/docs",
    }


def main():
    """启动服务"""
    import uvicorn

    uvicorn.run(
        "behavior_insight.main:app",
        host="0.0.0.0",
        port=settings.insight_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
