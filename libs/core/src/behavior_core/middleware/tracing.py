"""
链路追踪中间件

为每个请求生成唯一的 TraceID，便于日志追踪。
"""
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = structlog.get_logger()


class TraceIDMiddleware(BaseHTTPMiddleware):
    """
    TraceID 中间件

    为每个请求生成或传递 TraceID，便于日志追踪和问题排查。
    """

    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Trace-Id",
        generator: Callable[[], str] = lambda: str(uuid.uuid4()),
    ) -> None:
        """
        初始化 TraceID 中间件

        Args:
            app: FastAPI 应用
            header_name: TraceID 头名称
            generator: TraceID 生成函数
        """
        super().__init__(app)
        self.header_name = header_name
        self.generator = generator

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        处理请求

        Args:
            request: 请求对象
            call_next: 下一个处理器

        Returns:
            响应对象
        """
        # 从请求头获取或生成 TraceID
        trace_id = request.headers.get(self.header_name)
        if not trace_id:
            trace_id = self.generator()

        # 绑定到 structlog 上下文
        structlog.contextvars.bind_contextvars(
            trace_id=trace_id,
            request_id=trace_id,  # 兼容不同的命名
        )

        # 处理请求
        try:
            response = await call_next(request)
        finally:
            # 清理上下文
            structlog.contextvars.unbind_contextvars("trace_id", "request_id")

        # 将 TraceID 添加到响应头
        response.headers[self.header_name] = trace_id

        return response


def get_trace_id() -> str | None:
    """
    获取当前请求的 TraceID

    Returns:
        TraceID 字符串，如果不在请求上下文中则返回 None
    """
    context = structlog.contextvars.get_contextvars()
    return context.get("trace_id")
