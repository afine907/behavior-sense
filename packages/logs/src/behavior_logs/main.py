"""
BehaviorSense Logs Service
事件日志检索服务
"""
from contextlib import asynccontextmanager

from behavior_core.config.settings import get_settings
from behavior_core.middleware.tracing import TraceIDMiddleware
from behavior_core.utils.logging import get_logger, setup_logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from behavior_logs.routers.logs import router as logs_router

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    setup_logging()
    logger.info("logs_service_starting", port=settings.logs_port)
    yield
    logger.info("logs_service_stopping")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="BehaviorSense Logs Service",
        description="事件日志检索服务 - 查询和分析用户行为事件",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 中间件
    app.add_middleware(TraceIDMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 路由
    app.include_router(logs_router)

    # 根路径
    @app.get("/", tags=["root"])
    async def root():
        return {
            "service": "BehaviorSense Logs Service",
            "version": "1.0.0",
            "docs": "/docs",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "behavior_logs.main:app",
        host="0.0.0.0",
        port=settings.logs_port,
        reload=settings.debug,
    )
