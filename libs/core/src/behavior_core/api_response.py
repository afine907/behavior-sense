"""
标准化API响应格式
"""
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ApiResponse(BaseModel, Generic[T]):
    """标准化API响应"""
    success: bool = True
    data: T | None = None
    error: dict[str, Any] | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=_utc_now)

    @classmethod
    def ok(cls, data: T, meta: dict[str, Any] | None = None) -> "ApiResponse[T]":
        """成功响应"""
        return cls(success=True, data=data, meta=meta or {})

    @classmethod
    def error(
        cls,
        message: str,
        error_type: str = "internal_error",
        details: dict[str, Any] | None = None,
        status_code: int = 500,
    ) -> "ApiResponse":
        """错误响应"""
        return cls(
            success=False,
            error={
                "type": error_type,
                "message": message,
                "details": details or {},
                "status_code": status_code,
            },
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    success: bool = True
    data: list[T] = Field(default_factory=list)
    pagination: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=_utc_now)

    @classmethod
    def ok(
        cls,
        data: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """成功分页响应"""
        return cls(
            success=True,
            data=data,
            pagination={
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            },
        )


class ErrorResponse(BaseModel):
    """错误响应详情"""
    success: bool = False
    error: dict[str, Any]
    timestamp: datetime = Field(default_factory=_utc_now)


# Common error responses
def not_found(resource: str, identifier: str) -> ErrorResponse:
    """404错误"""
    return ErrorResponse(
        error={
            "type": "not_found",
            "message": f"{resource} '{identifier}' not found",
            "details": {"resource": resource, "identifier": identifier},
            "status_code": 404,
        }
    )


def validation_error(field: str, reason: str) -> ErrorResponse:
    """422验证错误"""
    return ErrorResponse(
        error={
            "type": "validation_error",
            "message": f"Validation failed for '{field}': {reason}",
            "details": {"field": field, "reason": reason},
            "status_code": 422,
        }
    )


def unauthorized(message: str = "Authentication required") -> ErrorResponse:
    """401未授权"""
    return ErrorResponse(
        error={
            "type": "unauthorized",
            "message": message,
            "status_code": 401,
        }
    )


def forbidden(message: str = "Access denied") -> ErrorResponse:
    """403禁止"""
    return ErrorResponse(
        error={
            "type": "forbidden",
            "message": message,
            "status_code": 403,
        }
    )


def rate_limit_exceeded(retry_after: int = 60) -> ErrorResponse:
    """429限流"""
    return ErrorResponse(
        error={
            "type": "rate_limit_exceeded",
            "message": f"Rate limit exceeded. Retry after {retry_after} seconds",
            "details": {"retry_after": retry_after},
            "status_code": 429,
        }
    )


def internal_error(message: str = "Internal server error") -> ErrorResponse:
    """500内部错误"""
    return ErrorResponse(
        error={
            "type": "internal_error",
            "message": message,
            "status_code": 500,
        }
    )
