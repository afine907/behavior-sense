"""
画像 API 路由
"""
from typing import Any

from behavior_core.models import UserProfile, UserStat
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from behavior_insight.repositories.user_repo import UserRepository
from behavior_insight.services.tag_service import TagService

router = APIRouter(prefix="/api/insight", tags=["profile"])


class ProfileUpdateRequest(BaseModel):
    """画像更新请求"""
    basic_info: dict[str, Any] | None = Field(default=None, description="基础信息")
    behavior_tags: list[str] | None = Field(default=None, description="行为标签")
    stat_tags: dict[str, Any] | None = Field(default=None, description="统计标签")
    predict_tags: dict[str, Any] | None = Field(default=None, description="预测标签")
    risk_level: str | None = Field(default=None, description="风险等级")


class TagStatisticsResponse(BaseModel):
    """标签统计响应"""
    total_users: int = Field(description="用户总数")
    tag_counts: dict[str, int] = Field(description="标签统计")


def get_user_repo(request: Request) -> UserRepository:
    """获取用户仓库依赖"""
    # 优先使用 request.state（由 middleware 设置），否则回退到 app.state
    if hasattr(request.state, "user_repo"):
        return request.state.user_repo
    return request.app.state.user_repo


def get_tag_service(request: Request) -> TagService:
    """获取标签服务依赖"""
    return request.app.state.tag_service


@router.get("/user/{user_id}/profile", response_model=UserProfile)
async def get_user_profile(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserProfile:
    """
    获取用户画像

    Args:
        user_id: 用户ID

    Returns:
        用户画像
    """
    profile = await user_repo.get_user_profile(user_id)

    if profile is None:
        raise HTTPException(status_code=404, detail="User profile not found")

    return profile


@router.put("/user/{user_id}/profile", response_model=UserProfile)
async def update_user_profile(
    user_id: str,
    request: ProfileUpdateRequest,
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserProfile:
    """
    更新用户画像

    Args:
        user_id: 用户ID
        request: 画像更新请求

    Returns:
        更新后的用户画像
    """
    # 获取现有画像
    existing = await user_repo.get_user_profile(user_id)

    if existing is None:
        # 创建新画像
        update_data: dict[str, Any] = {
            "basic_info": request.basic_info or {},
            "behavior_tags": request.behavior_tags or [],
            "stat_tags": request.stat_tags or {},
            "predict_tags": request.predict_tags or {},
            "risk_level": request.risk_level or "low",
        }
    else:
        # 更新现有画像
        update_data = {}
        if request.basic_info is not None:
            update_data["basic_info"] = request.basic_info
        if request.behavior_tags is not None:
            update_data["behavior_tags"] = request.behavior_tags
        if request.stat_tags is not None:
            update_data["stat_tags"] = request.stat_tags
        if request.predict_tags is not None:
            update_data["predict_tags"] = request.predict_tags
        if request.risk_level is not None:
            update_data["risk_level"] = request.risk_level

    profile = await user_repo.update_user_profile(user_id, update_data)
    return profile


@router.get("/user/{user_id}/stat", response_model=UserStat)
async def get_user_stat(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserStat:
    """
    获取用户统计

    Args:
        user_id: 用户ID

    Returns:
        用户统计数据
    """
    stat = await user_repo.get_user_stat(user_id)

    if stat is None:
        raise HTTPException(status_code=404, detail="User stats not found")

    return stat


@router.get("/tags/statistics", response_model=TagStatisticsResponse)
async def get_tag_statistics(
    user_repo: UserRepository = Depends(get_user_repo),
    tag_service: TagService = Depends(get_tag_service),
) -> TagStatisticsResponse:
    """
    获取标签统计

    Returns:
        标签统计信息
    """
    # 获取用户总数
    total_users = await user_repo.count_users()

    # 获取标签统计
    tag_counts = await tag_service.get_tag_statistics()

    return TagStatisticsResponse(
        total_users=total_users,
        tag_counts=tag_counts,
    )


@router.get("/users/by-risk/{risk_level}")
async def get_users_by_risk(
    risk_level: str,
    user_repo: UserRepository = Depends(get_user_repo),
) -> dict[str, Any]:
    """
    获取指定风险等级的用户列表

    Args:
        risk_level: 风险等级 (low, medium, high)

    Returns:
        用户ID列表
    """
    if risk_level not in ("low", "medium", "high"):
        raise HTTPException(
            status_code=400,
            detail="Invalid risk level. Must be low, medium, or high",
        )

    user_ids = await user_repo.get_users_by_risk_level(risk_level)

    return {
        "risk_level": risk_level,
        "user_count": len(user_ids),
        "user_ids": user_ids,
    }


@router.delete("/user/{user_id}")
async def delete_user(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repo),
    tag_service: TagService = Depends(get_tag_service),
) -> dict[str, Any]:
    """
    删除用户（包括画像、统计和标签）

    Args:
        user_id: 用户ID

    Returns:
        删除结果
    """
    # 删除用户画像和统计
    deleted = await user_repo.delete_user(user_id)

    # 删除用户标签
    user_tags = await tag_service.get_user_tags(user_id)
    if user_tags:
        for tag_name in user_tags.tags.keys():
            await tag_service.remove_tag(user_id, tag_name)

    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "status": "ok",
        "user_id": user_id,
        "deleted": True,
    }
