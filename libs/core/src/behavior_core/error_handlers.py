"""
FastAPI错误处理器
"""
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from behavior_core.api_response import ErrorResponse
from behavior_core.exceptions import (
    AgentNotFoundError,
    BehaviorSenseError,
    CostLimitExceededError,
    RuleEvaluationError,
    StreamProcessingError,
    ValidationError,
)

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    """注册全局错误处理器"""

    @app.exception_handler(AgentNotFoundError)
    async def agent_not_found_handler(request: Request, exc: AgentNotFoundError):
        logger.warning(f"Agent not found: {exc.message}")
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error={
                    "type": "not_found",
                    "message": exc.message,
                    "details": exc.details,
                    "status_code": 404,
                }
            ).model_dump(),
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        logger.warning(f"Validation error: {exc.message}")
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error={
                    "type": "validation_error",
                    "message": exc.message,
                    "details": exc.details,
                    "status_code": 422,
                }
            ).model_dump(),
        )

    @app.exception_handler(CostLimitExceededError)
    async def cost_limit_handler(request: Request, exc: CostLimitExceededError):
        logger.warning(f"Cost limit exceeded: {exc.message}")
        return JSONResponse(
            status_code=402,
            content=ErrorResponse(
                error={
                    "type": "cost_limit_exceeded",
                    "message": exc.message,
                    "details": exc.details,
                    "status_code": 402,
                }
            ).model_dump(),
        )

    @app.exception_handler(RuleEvaluationError)
    async def rule_evaluation_handler(request: Request, exc: RuleEvaluationError):
        logger.error(f"Rule evaluation error: {exc.message}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error={
                    "type": "rule_evaluation_error",
                    "message": exc.message,
                    "details": exc.details,
                    "status_code": 500,
                }
            ).model_dump(),
        )

    @app.exception_handler(BehaviorSenseError)
    async def base_error_handler(request: Request, exc: BehaviorSenseError):
        logger.error(f"BehaviorSense error: {exc.message}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error={
                    "type": "internal_error",
                    "message": exc.message,
                    "details": exc.details,
                    "status_code": 500,
                }
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error={
                    "type": "internal_error",
                    "message": "An unexpected error occurred",
                    "details": {"error": str(exc)},
                    "status_code": 500,
                }
            ).model_dump(),
        )
