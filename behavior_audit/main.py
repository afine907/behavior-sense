"""
BehaviorSense Audit Service
人工审核服务
"""
from contextlib import asynccontextmanager
from datetime import datetime

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from behavior_core.config.settings import get_settings
from behavior_core.utils.logging import setup_logging, get_logger
from behavior_audit.routers.audit import router as audit_router
from behavior_audit.repositories.audit_repo import init_db, get_engine

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    setup_logging()
    logger.info("Starting audit service", version="1.0.0")

    # 初始化数据库
    await init_db()
    logger.info("Database initialized")

    # 初始化 Redis 连接
    app.state.redis = redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        max_connections=settings.redis_max_connections,
    )
    logger.info("Redis connected")

    yield

    # 关闭时
    logger.info("Shutting down audit service")

    # 关闭 Redis
    await app.state.redis.close()
    logger.info("Redis connection closed")

    # 关闭数据库连接池
    engine = await get_engine()
    await engine.dispose()
    logger.info("Database connection pool disposed")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="BehaviorSense Audit Service",
        description="人工审核服务 - 管理用户行为审核工单",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(audit_router)

    # 健康检查端点
    @app.get("/health", tags=["health"])
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "service": "behavior_audit",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
        }

    # 根路径
    @app.get("/", tags=["root"])
    async def root():
        """服务根路径"""
        return {
            "service": "BehaviorSense Audit Service",
            "version": "1.0.0",
            "docs": "/docs",
        }

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "behavior_audit.main:app",
        host="0.0.0.0",
        port=settings.audit_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
