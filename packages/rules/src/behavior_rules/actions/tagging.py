"""
打标签动作处理器

实现用户标签管理功能，通过调用 insight 服务 API 实现标签操作。
"""
import logging
from typing import Any

import httpx
from behavior_core.config.settings import settings

logger = logging.getLogger(__name__)


# 共享 HTTP 客户端实例（懒加载）
_shared_client: httpx.AsyncClient | None = None


async def get_shared_client() -> httpx.AsyncClient:
    """
    获取共享的 HTTP 客户端实例

    复用连接，避免每次请求都创建新连接。
    """
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0,
            ),
        )
    return _shared_client


async def close_shared_client() -> None:
    """关闭共享的 HTTP 客户端"""
    global _shared_client
    if _shared_client is not None:
        await _shared_client.aclose()
        _shared_client = None


class TaggingError(Exception):
    """打标签异常"""
    pass


async def tag_user(params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """
    为用户打标签

    调用 insight 服务 API 更新用户标签。

    Args:
        params: 动作参数，包含:
            - tags: 要添加的标签列表
            - action: 操作类型 (add/remove/set)，默认 add
            - source: 标签来源，默认 "rule"
            - ttl: 标签有效期（秒），可选
        context: 执行上下文，包含 user_id 等信息

    Returns:
        执行结果，包含状态和响应数据

    Raises:
        TaggingError: 打标签失败
    """
    user_id = context.get("user_id")
    if not user_id:
        raise TaggingError("Missing user_id in context")

    tags = params.get("tags", [])
    if not tags:
        raise TaggingError("Missing tags parameter")

    action = params.get("action", "add")
    source = params.get("source", "rule")
    ttl = params.get("ttl")

    # 构建 insight 服务 URL
    insight_host = params.get("insight_host", "localhost")
    insight_port = params.get("insight_port", settings.insight_port)
    base_url = f"http://{insight_host}:{insight_port}"

    # 构建请求体
    request_body: dict[str, Any] = {
        "tags": tags,
        "source": source,
    }
    if ttl:
        request_body["ttl"] = ttl

    try:
        # 使用共享客户端
        client = await get_shared_client()

        if action == "add":
            # 添加标签
            response = await client.put(
                f"{base_url}/api/insight/user/{user_id}/tags",
                json=request_body
            )
        elif action == "remove":
            # 移除标签
            response = await client.request(
                "DELETE",
                f"{base_url}/api/insight/user/{user_id}/tags",
                json=request_body
            )
        elif action == "set":
            # 设置标签（覆盖）
            response = await client.post(
                f"{base_url}/api/insight/user/{user_id}/tags",
                json=request_body
            )
        else:
            raise TaggingError(f"Unknown action: {action}")

        if response.status_code >= 400:
            error_detail = response.text
            logger.error(
                f"Failed to tag user {user_id}: "
                f"status={response.status_code}, error={error_detail}"
            )
            raise TaggingError(
                f"Insight service returned {response.status_code}: {error_detail}"
            )

        result = response.json() if response.content else {}
        logger.info(f"Successfully tagged user {user_id} with {tags}")

        return {
            "status": "success",
            "user_id": user_id,
            "tags": tags,
            "action": action,
            "response": result
        }

    except httpx.TimeoutException:
        logger.error(f"Timeout while tagging user {user_id}")
        raise TaggingError("Insight service timeout")
    except httpx.RequestError as e:
        logger.error(f"Request error while tagging user {user_id}: {e}")
        raise TaggingError(f"Request error: {e}")


async def get_user_tags(
    user_id: str,
    insight_host: str = "localhost",
    insight_port: int | None = None
) -> dict[str, Any]:
    """
    获取用户标签

    Args:
        user_id: 用户ID
        insight_host: insight 服务主机
        insight_port: insight 服务端口

    Returns:
        用户标签数据
    """
    port = insight_port or settings.insight_port
    base_url = f"http://{insight_host}:{port}"

    try:
        client = await get_shared_client()
        response = await client.get(
            f"{base_url}/api/insight/user/{user_id}/tags"
        )

        if response.status_code == 404:
            return {"user_id": user_id, "tags": {}}

        if response.status_code >= 400:
            raise TaggingError(
                f"Failed to get user tags: status={response.status_code}"
            )

        return response.json()

    except httpx.TimeoutException:
        raise TaggingError("Insight service timeout")
    except httpx.RequestError as e:
        raise TaggingError(f"Request error: {e}")


async def batch_tag_users(
    users_tags: list[dict[str, Any]],
    insight_host: str = "localhost",
    insight_port: int | None = None
) -> list[dict[str, Any]]:
    """
    批量为用户打标签

    Args:
        users_tags: 用户标签列表，每项包含 user_id 和 tags
        insight_host: insight 服务主机
        insight_port: insight 服务端口

    Returns:
        批量操作结果
    """
    import asyncio

    results = []
    port = insight_port or settings.insight_port
    base_url = f"http://{insight_host}:{port}"

    client = await get_shared_client()

    async def tag_single_user(item: dict[str, Any]) -> dict[str, Any]:
        user_id = item.get("user_id")
        tags = item.get("tags", [])

        if not user_id or not tags:
            return {
                "user_id": user_id,
                "status": "error",
                "error": "Missing user_id or tags"
            }

        try:
            response = await client.put(
                f"{base_url}/api/insight/user/{user_id}/tags",
                json={"tags": tags, "source": "batch_rule"}
            )

            return {
                "user_id": user_id,
                "status": "success" if response.status_code < 400 else "error",
                "status_code": response.status_code
            }

        except Exception as e:
            return {
                "user_id": user_id,
                "status": "error",
                "error": str(e)
            }

    # 并发处理批量请求
    results = await asyncio.gather(*[tag_single_user(item) for item in users_tags])
    return list(results)
