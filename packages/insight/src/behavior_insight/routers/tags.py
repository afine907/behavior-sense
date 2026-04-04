"""
标签 API 路由
"""
from datetime import datetime
from typing import Any

from behavior_core.models import TagSource, UserTags
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from behavior_insight.services.tag_service import TagService

router = APIRouter(prefix="/api/insight/user", tags=["tags"])


class TagUpdateRequest(BaseModel):
    """标签更新请求"""
    tag_name: str = Field(..., description="标签名")
    tag_value: str = Field(..., description="标签值")
    source: TagSource = Field(default=TagSource.MANUAL, description="标签来源")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度")
    expire_at: datetime | None = Field(default=None, description="过期时间")


class BatchQueryRequest(BaseModel):
    """批量查询请求"""
    user_ids: list[str] = Field(..., description="用户ID列表")
    tag_names: list[str] | None = Field(default=None, description="标签名列表")


class BatchQueryResponse(BaseModel):
    """批量查询响应"""
    results: dict[str, dict[str, Any]] = Field(default_factory=dict)


def get_tag_service(request: Request) -> TagService:
    """获取标签服务依赖"""
    return request.app.state.tag_service


@router.get("/{user_id}/tags", response_model=UserTags)
async def get_user_tags(
    user_id: str,
    tag_service: TagService = Depends(get_tag_service),
) -> UserTags:
    """
    获取用户标签

    Args:
        user_id: 用户ID

    Returns:
        用户的所有标签
    """
    user_tags = await tag_service.get_user_tags(user_id)

    if user_tags is None:
        raise HTTPException(status_code=404, detail="User tags not found")

    return user_tags


@router.put("/{user_id}/tag")
async def update_user_tag(
    user_id: str,
    request: TagUpdateRequest,
    tag_service: TagService = Depends(get_tag_service),
) -> dict[str, Any]:
    """
    更新用户标签

    Args:
        user_id: 用户ID
        request: 标签更新请求

    Returns:
        更新结果
    """
    tag_value = await tag_service.update_tag(
        user_id=user_id,
        tag_name=request.tag_name,
        value=request.tag_value,
        source=request.source,
        confidence=request.confidence,
        expire_at=request.expire_at,
    )

    return {
        "status": "ok",
        "user_id": user_id,
        "tag_name": request.tag_name,
        "tag_value": tag_value.model_dump(),
    }


@router.delete("/{user_id}/tag/{tag_name}")
async def delete_user_tag(
    user_id: str,
    tag_name: str,
    tag_service: TagService = Depends(get_tag_service),
) -> dict[str, Any]:
    """
    删除用户标签

    Args:
        user_id: 用户ID
        tag_name: 标签名

    Returns:
        删除结果
    """
    removed = await tag_service.remove_tag(user_id, tag_name)

    if not removed:
        raise HTTPException(
            status_code=404, detail="Tag not found for user"
        )

    return {
        "status": "ok",
        "user_id": user_id,
        "tag_name": tag_name,
        "removed": True,
    }


@router.post("/tags/batch", response_model=BatchQueryResponse)
async def batch_get_tags(
    request: BatchQueryRequest,
    tag_service: TagService = Depends(get_tag_service),
) -> BatchQueryResponse:
    """
    批量查询用户标签

    Args:
        request: 批量查询请求

    Returns:
        批量查询结果
    """
    if len(request.user_ids) > 100:
        raise HTTPException(
            status_code=400, detail="Maximum 100 users per batch"
        )

    results = await tag_service.batch_get_tags(
        user_ids=request.user_ids,
        tag_names=request.tag_names,
    )

    # 转换 TagValue 为可序列化格式
    serializable_results: dict[str, dict[str, Any]] = {}
    for user_id, tags in results.items():
        serializable_results[user_id] = {
            name: value.model_dump() for name, value in tags.items()
        }

    return BatchQueryResponse(results=serializable_results)


@router.get("/tags/by-value")
async def get_users_by_tag(
    tag_name: str,
    tag_value: str | None = None,
    tag_service: TagService = Depends(get_tag_service),
) -> dict[str, Any]:
    """
    根据标签获取用户列表

    Args:
        tag_name: 标签名
        tag_value: 标签值（可选）

    Returns:
        用户ID列表
    """
    user_ids = await tag_service.get_users_by_tag(tag_name, tag_value)

    return {
        "tag_name": tag_name,
        "tag_value": tag_value,
        "user_count": len(user_ids),
        "user_ids": user_ids,
    }
