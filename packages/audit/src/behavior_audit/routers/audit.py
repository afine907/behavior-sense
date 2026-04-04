"""
审核 API 路由
"""
from datetime import datetime
from typing import Any

from behavior_core.utils.logging import get_logger
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from behavior_audit.repositories.audit_repo import (
    AuditLevel,
    AuditRepository,
    get_session,
)
from behavior_audit.services.audit_service import (
    AuditService,
    InvalidStatusTransitionError,
    OrderNotFoundError,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit"])


# ============== 请求/响应模型 ==============

class CreateOrderRequest(BaseModel):
    """创建审核工单请求"""
    user_id: str = Field(..., description="用户ID")
    rule_id: str = Field(..., description="触发的规则ID")
    trigger_data: dict[str, Any] = Field(default_factory=dict, description="触发数据")
    audit_level: str = Field(default=AuditLevel.MEDIUM.value, description="审核级别")


class AssignOrderRequest(BaseModel):
    """分配审核人请求"""
    assignee: str = Field(..., description="审核人ID")


class ReviewRequest(BaseModel):
    """提交审核请求"""
    status: str = Field(..., description="审核状态 (approved/rejected/closed)")
    note: str | None = Field(default=None, description="审核备注")
    reviewer: str | None = Field(default=None, description="审核人ID")


class BatchAssignRequest(BaseModel):
    """批量分配请求"""
    order_ids: list[str] = Field(..., description="工单ID列表")
    assignee: str = Field(..., description="审核人ID")


class OrderResponse(BaseModel):
    """工单响应"""
    id: str
    user_id: str
    rule_id: str
    trigger_data: dict[str, Any]
    audit_level: str
    status: str
    assignee: str | None
    reviewer_note: str | None
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """工单列表响应"""
    items: list[OrderResponse]
    total: int
    page: int
    size: int


class StatsResponse(BaseModel):
    """统计响应"""
    status_counts: dict[str, int]
    level_counts: dict[str, int]
    today_count: int


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: datetime


# ============== 依赖注入 ==============

async def get_repository(
    session: AsyncSession = Depends(get_session)
) -> AuditRepository:
    """获取仓库实例"""
    return AuditRepository(session)


async def get_service(
    repo: AuditRepository = Depends(get_repository)
) -> AuditService:
    """获取服务实例"""
    return AuditService(repo)


# ============== API 端点 ==============

@router.post("/order", response_model=OrderResponse, status_code=201)
async def create_order(
    request: CreateOrderRequest,
    service: AuditService = Depends(get_service),
) -> OrderResponse:
    """
    创建审核工单

    当规则引擎检测到需要人工审核的情况时，调用此接口创建审核工单。
    """
    try:
        order = await service.create_order(
            user_id=request.user_id,
            rule_id=request.rule_id,
            trigger_data=request.trigger_data,
            level=request.audit_level,
        )
        return OrderResponse.model_validate(order)
    except Exception as e:
        logger.error("Failed to create order", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/order/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    service: AuditService = Depends(get_service),
) -> OrderResponse:
    """
    获取工单详情

    根据工单ID获取审核工单的详细信息。
    """
    try:
        order = await service.get_order(order_id)
        return OrderResponse.model_validate(order)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail="Order not found")


@router.put("/order/{order_id}/assign", response_model=OrderResponse)
async def assign_order(
    order_id: str,
    request: AssignOrderRequest,
    service: AuditService = Depends(get_service),
) -> OrderResponse:
    """
    分配审核人

    将审核工单分配给指定的审核人员。工单状态会从 pending 变为 in_review。
    """
    try:
        order = await service.assign_order(order_id, request.assignee)
        return OrderResponse.model_validate(order)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail="Order not found")
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/order/{order_id}/review", response_model=OrderResponse)
async def submit_review(
    order_id: str,
    request: ReviewRequest,
    service: AuditService = Depends(get_service),
) -> OrderResponse:
    """
    提交审核结果

    审核人员提交审核结果。状态可以是：
    - approved: 审核通过
    - rejected: 审核驳回
    - closed: 关闭工单
    """
    try:
        order = await service.submit_review(
            order_id=order_id,
            status=request.status,
            note=request.note,
            reviewer=request.reviewer,
        )
        return OrderResponse.model_validate(order)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail="Order not found")
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders", response_model=OrderListResponse)
async def list_orders(
    status: str | None = Query(default=None, description="状态过滤"),
    assignee: str | None = Query(default=None, description="审核人过滤"),
    user_id: str | None = Query(default=None, description="用户ID过滤"),
    page: int = Query(default=1, ge=1, description="页码"),
    size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    service: AuditService = Depends(get_service),
) -> OrderListResponse:
    """
    查询工单列表

    支持按状态、审核人、用户ID过滤，支持分页。
    """
    orders, total = await service.list_orders(
        status=status,
        assignee=assignee,
        user_id=user_id,
        page=page,
        size=size,
    )
    items = [OrderResponse.model_validate(o) for o in orders]
    return OrderListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.get("/orders/todo", response_model=list[OrderResponse])
async def get_todo_orders(
    assignee: str = Query(..., description="审核人ID"),
    service: AuditService = Depends(get_service),
) -> list[OrderResponse]:
    """
    获取待办列表

    获取分配给指定审核人的待处理工单。
    返回 pending 和 in_review 状态的工单，按优先级和创建时间排序。
    """
    orders = await service.get_todo_list(assignee)
    return [OrderResponse.model_validate(o) for o in orders]


@router.get("/orders/unassigned", response_model=list[OrderResponse])
async def get_unassigned_orders(
    service: AuditService = Depends(get_service),
) -> list[OrderResponse]:
    """
    获取未分配的待处理工单

    返回所有未分配审核人的待处理工单。
    """
    orders = await service.get_unassigned_pending()
    return [OrderResponse.model_validate(o) for o in orders]


@router.post("/orders/batch-assign", response_model=list[OrderResponse])
async def batch_assign_orders(
    request: BatchAssignRequest,
    service: AuditService = Depends(get_service),
) -> list[OrderResponse]:
    """
    批量分配审核人

    将多个工单批量分配给同一个审核人。
    """
    orders = await service.batch_assign(request.order_ids, request.assignee)
    return [OrderResponse.model_validate(o) for o in orders]


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    service: AuditService = Depends(get_service),
) -> StatsResponse:
    """
    获取审核统计

    返回各状态、各级别的工单数量统计，以及今日新增数量。
    """
    stats = await service.get_stats()
    return StatsResponse(**stats)


@router.put("/order/{order_id}/reopen", response_model=OrderResponse)
async def reopen_order(
    order_id: str,
    assignee: str | None = Query(default=None, description="新审核人"),
    service: AuditService = Depends(get_service),
) -> OrderResponse:
    """
    重新打开工单

    从驳回状态重新打开工单进行审核。
    """
    try:
        order = await service.reopen_order(order_id, assignee)
        return OrderResponse.model_validate(order)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail="Order not found")


@router.delete("/order/{order_id}", status_code=204)
async def delete_order(
    order_id: str,
    repo: AuditRepository = Depends(get_repository),
) -> None:
    """
    删除工单

    删除指定的审核工单（谨慎使用）。
    """
    deleted = await repo.delete(order_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Order not found")
