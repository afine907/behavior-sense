"""
审核动作处理器

实现触发人工审核的功能，通过调用 audit 服务 API 创建审核工单。
"""
import asyncio
import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import httpx
from behavior_core.config.settings import settings

logger = logging.getLogger(__name__)


# 共享 HTTP 客户端实例（懒加载）
_audit_client: httpx.AsyncClient | None = None


async def get_audit_client() -> httpx.AsyncClient:
    """
    获取共享的 HTTP 客户端实例（用于 audit 服务）

    复用连接，避免每次请求都创建新连接。
    """
    global _audit_client
    if _audit_client is None or _audit_client.is_closed:
        _audit_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0,
            ),
        )
    return _audit_client


async def close_audit_client() -> None:
    """关闭共享的 HTTP 客户端"""
    global _audit_client
    if _audit_client is not None:
        await _audit_client.aclose()
        _audit_client = None


class AuditLevel(str, Enum):
    """审核级别"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AuditTriggerError(Exception):
    """审核触发异常"""
    pass


async def trigger_audit(params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """
    触发人工审核

    调用 audit 服务 API 创建审核工单。

    Args:
        params: 动作参数，包含:
            - level: 审核级别 (LOW/MEDIUM/HIGH/CRITICAL)
            - reason: 审核原因
            - rule_id: 触发规则ID，可选
            - assignee: 指派审核人，可选
            - metadata: 额外元数据，可选
        context: 执行上下文，包含 user_id 等信息

    Returns:
        执行结果，包含工单ID和状态

    Raises:
        AuditTriggerError: 触发审核失败
    """
    user_id = context.get("user_id")
    if not user_id:
        raise AuditTriggerError("Missing user_id in context")

    level = params.get("level", "MEDIUM")
    reason = params.get("reason", "Rule triggered audit")
    rule_id = params.get("rule_id") or context.get("rule_id")
    assignee = params.get("assignee")
    metadata = params.get("metadata", {})

    # 验证审核级别
    try:
        audit_level = AuditLevel(level.upper())
    except ValueError:
        logger.warning(f"Invalid audit level: {level}, using MEDIUM")
        audit_level = AuditLevel.MEDIUM

    # 构建 audit 服务 URL
    audit_host = params.get("audit_host", "localhost")
    audit_port = params.get("audit_port", settings.audit_port)
    base_url = f"http://{audit_host}:{audit_port}"

    # 构建工单请求
    order_request: dict[str, Any] = {
        "user_id": user_id,
        "audit_level": audit_level.value,
        "reason": reason,
        "trigger_data": {
            "rule_id": rule_id,
            "context": context,
            "triggered_at": datetime.now(UTC).isoformat(),
            **metadata
        }
    }

    if assignee:
        order_request["assignee"] = assignee

    try:
        client = await get_audit_client()
        response = await client.post(
            f"{base_url}/api/audit/order",
            json=order_request
        )

        if response.status_code >= 400:
            error_detail = response.text
            logger.error(
                f"Failed to create audit order for user {user_id}: "
                f"status={response.status_code}, error={error_detail}"
            )
            raise AuditTriggerError(
                f"Audit service returned {response.status_code}: {error_detail}"
            )

        result = response.json()
        order_id = result.get("order_id") or result.get("id")

        logger.info(
            f"Created audit order {order_id} for user {user_id} "
            f"with level {audit_level.value}"
        )

        return {
            "status": "success",
            "order_id": order_id,
            "user_id": user_id,
            "audit_level": audit_level.value,
            "reason": reason,
            "response": result
        }

    except httpx.TimeoutException:
        logger.error(f"Timeout while creating audit order for user {user_id}")
        raise AuditTriggerError("Audit service timeout")
    except httpx.RequestError as e:
        logger.error(f"Request error while creating audit order: {e}")
        raise AuditTriggerError(f"Request error: {e}")


async def get_audit_order(
    order_id: str,
    audit_host: str = "localhost",
    audit_port: int | None = None
) -> dict[str, Any]:
    """
    获取审核工单详情

    Args:
        order_id: 工单ID
        audit_host: audit 服务主机
        audit_port: audit 服务端口

    Returns:
        工单详情
    """
    port = audit_port or settings.audit_port
    base_url = f"http://{audit_host}:{port}"

    try:
        client = await get_audit_client()
        response = await client.get(
            f"{base_url}/api/audit/order/{order_id}"
        )

        if response.status_code == 404:
            raise AuditTriggerError(f"Audit order not found: {order_id}")

        if response.status_code >= 400:
            raise AuditTriggerError(
                f"Failed to get audit order: status={response.status_code}"
            )

        return response.json()

    except httpx.TimeoutException:
        raise AuditTriggerError("Audit service timeout")
    except httpx.RequestError as e:
        raise AuditTriggerError(f"Request error: {e}")


async def get_pending_audits(
    audit_host: str = "localhost",
    audit_port: int | None = None,
    limit: int = 100
) -> list[dict[str, Any]]:
    """
    获取待审核工单列表

    Args:
        audit_host: audit 服务主机
        audit_port: audit 服务端口
        limit: 返回数量限制

    Returns:
        待审核工单列表
    """
    port = audit_port or settings.audit_port
    base_url = f"http://{audit_host}:{port}"

    try:
        client = await get_audit_client()
        response = await client.get(
            f"{base_url}/api/audit/orders/todo",
            params={"limit": limit}
        )

        if response.status_code >= 400:
            raise AuditTriggerError(
                f"Failed to get pending audits: status={response.status_code}"
            )

        return response.json()

    except httpx.TimeoutException:
        raise AuditTriggerError("Audit service timeout")
    except httpx.RequestError as e:
        raise AuditTriggerError(f"Request error: {e}")


async def submit_review(
    order_id: str,
    status: str,
    reviewer_note: str | None = None,
    audit_host: str = "localhost",
    audit_port: int | None = None
) -> dict[str, Any]:
    """
    提交审核结果

    Args:
        order_id: 工单ID
        status: 审核状态 (approved/rejected)
        reviewer_note: 审核备注
        audit_host: audit 服务主机
        audit_port: audit 服务端口

    Returns:
        审核结果
    """
    port = audit_port or settings.audit_port
    base_url = f"http://{audit_host}:{port}"

    request_body: dict[str, Any] = {"status": status}
    if reviewer_note:
        request_body["reviewer_note"] = reviewer_note

    try:
        client = await get_audit_client()
        response = await client.put(
            f"{base_url}/api/audit/order/{order_id}/review",
            json=request_body
        )

        if response.status_code >= 400:
            raise AuditTriggerError(
                f"Failed to submit review: status={response.status_code}"
            )

        return response.json()

    except httpx.TimeoutException:
        raise AuditTriggerError("Audit service timeout")
    except httpx.RequestError as e:
        raise AuditTriggerError(f"Request error: {e}")


async def batch_trigger_audit(
    users: list[dict[str, Any]],
    audit_host: str = "localhost",
    audit_port: int | None = None
) -> list[dict[str, Any]]:
    """
    批量触发审核（并发处理）

    Args:
        users: 用户列表，每项包含 user_id 和相关参数
        audit_host: audit 服务主机
        audit_port: audit 服务端口

    Returns:
        批量操作结果
    """
    port = audit_port or settings.audit_port
    base_url = f"http://{audit_host}:{port}"
    client = await get_audit_client()

    async def trigger_single(item: dict[str, Any]) -> dict[str, Any]:
        user_id = item.get("user_id")
        if not user_id:
            return {
                "user_id": None,
                "status": "error",
                "error": "Missing user_id"
            }

        try:
            response = await client.post(
                f"{base_url}/api/audit/order",
                json={
                    "user_id": user_id,
                    "audit_level": item.get("level", "MEDIUM"),
                    "reason": item.get("reason", "Batch audit"),
                    "trigger_data": item.get("trigger_data", {})
                }
            )

            if response.status_code >= 400:
                return {
                    "user_id": user_id,
                    "status": "error",
                    "status_code": response.status_code
                }
            else:
                result = response.json()
                return {
                    "user_id": user_id,
                    "status": "success",
                    "order_id": result.get("order_id") or result.get("id")
                }

        except Exception as e:
            return {
                "user_id": user_id,
                "status": "error",
                "error": str(e)
            }

    # 并发处理
    results = await asyncio.gather(*[trigger_single(item) for item in users])
    return list(results)
