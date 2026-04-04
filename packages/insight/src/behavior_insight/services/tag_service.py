"""
标签服务
使用 Redis 存储标签数据
"""
import json
from datetime import datetime
from typing import Any

import redis.asyncio as redis
from behavior_core.models import TagSource, TagValue, UserTags
from behavior_core.utils.logging import get_logger

logger = get_logger(__name__)


class TagService:
    """标签服务 - 管理用户标签的存储和查询"""

    # Redis key 前缀
    TAG_KEY_PREFIX = "user:tags:"
    TAG_INDEX_KEY = "tags:index"

    def __init__(self, redis_client: redis.Redis):
        """
        初始化标签服务

        Args:
            redis_client: Redis 异步客户端
        """
        self._redis = redis_client

    def _get_tag_key(self, user_id: str) -> str:
        """获取用户标签的 Redis key"""
        return f"{self.TAG_KEY_PREFIX}{user_id}"

    async def get_user_tags(self, user_id: str) -> UserTags | None:
        """
        获取用户的所有标签

        Args:
            user_id: 用户ID

        Returns:
            UserTags 对象，如果用户不存在则返回 None
        """
        key = self._get_tag_key(user_id)
        tags_data = await self._redis.hgetall(key)

        if not tags_data:
            return None

        tags: dict[str, TagValue] = {}
        for tag_name, tag_json in tags_data.items():
            try:
                tag_dict = json.loads(tag_json)
                tags[tag_name] = TagValue(
                    value=tag_dict["value"],
                    timestamp=datetime.fromisoformat(tag_dict["timestamp"]),
                    confidence=tag_dict.get("confidence", 1.0),
                    source=TagSource(tag_dict.get("source", "auto")),
                    expire_at=datetime.fromisoformat(tag_dict["expire_at"])
                    if tag_dict.get("expire_at")
                    else None,
                )
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(
                    "Failed to parse tag",
                    user_id=user_id,
                    tag_name=tag_name,
                    error=str(e),
                )
                continue

        return UserTags(
            user_id=user_id,
            tags=tags,
            last_update=datetime.utcnow(),
        )

    async def update_tag(
        self,
        user_id: str,
        tag_name: str,
        value: str,
        source: TagSource = TagSource.AUTO,
        confidence: float = 1.0,
        expire_at: datetime | None = None,
    ) -> TagValue:
        """
        更新用户标签

        Args:
            user_id: 用户ID
            tag_name: 标签名
            value: 标签值
            source: 标签来源
            confidence: 置信度
            expire_at: 过期时间

        Returns:
            更新后的标签值
        """
        now = datetime.utcnow()
        tag_value = TagValue(
            value=value,
            timestamp=now,
            confidence=confidence,
            source=source,
            expire_at=expire_at,
        )

        tag_dict: dict[str, Any] = {
            "value": value,
            "timestamp": now.isoformat(),
            "confidence": confidence,
            "source": source.value,
        }
        if expire_at:
            tag_dict["expire_at"] = expire_at.isoformat()

        key = self._get_tag_key(user_id)
        await self._redis.hset(key, tag_name, json.dumps(tag_dict))

        # 更新标签索引
        await self._redis.sadd(f"{self.TAG_INDEX_KEY}:{tag_name}", user_id)

        # 发布标签更新事件
        await self._redis.publish(
            "tag:updates",
            json.dumps(
                {
                    "user_id": user_id,
                    "tag_name": tag_name,
                    "value": value,
                    "source": source.value,
                    "timestamp": now.isoformat(),
                }
            ),
        )

        logger.info(
            "Tag updated",
            user_id=user_id,
            tag_name=tag_name,
            value=value,
            source=source.value,
        )

        return tag_value

    async def batch_get_tags(
        self,
        user_ids: list[str],
        tag_names: list[str] | None = None,
    ) -> dict[str, dict[str, TagValue]]:
        """
        批量获取多个用户的标签

        Args:
            user_ids: 用户ID列表
            tag_names: 要获取的标签名列表，为空则获取所有标签

        Returns:
            用户ID -> 标签名 -> 标签值 的映射
        """
        result: dict[str, dict[str, TagValue]] = {}

        # 使用 pipeline 批量查询
        async with self._redis.pipeline() as pipe:
            for user_id in user_ids:
                key = self._get_tag_key(user_id)
                if tag_names:
                    for tag_name in tag_names:
                        pipe.hget(key, tag_name)
                else:
                    pipe.hgetall(key)

            responses = await pipe.execute()

        # 解析结果
        for i, user_id in enumerate(user_ids):
            result[user_id] = {}

            if tag_names:
                # 按标签名顺序获取结果
                for j, tag_name in enumerate(tag_names):
                    tag_json = responses[i * len(tag_names) + j]
                    if tag_json:
                        try:
                            tag_dict = json.loads(tag_json)
                            result[user_id][tag_name] = TagValue(
                                value=tag_dict["value"],
                                timestamp=datetime.fromisoformat(
                                    tag_dict["timestamp"]
                                ),
                                confidence=tag_dict.get("confidence", 1.0),
                                source=TagSource(
                                    tag_dict.get("source", "auto")
                                ),
                            )
                        except (json.JSONDecodeError, KeyError, ValueError):
                            pass
            else:
                # 获取所有标签
                tags_data = responses[i]
                if tags_data:
                    for tag_name, tag_json in tags_data.items():
                        try:
                            tag_dict = json.loads(tag_json)
                            result[user_id][tag_name] = TagValue(
                                value=tag_dict["value"],
                                timestamp=datetime.fromisoformat(
                                    tag_dict["timestamp"]
                                ),
                                confidence=tag_dict.get("confidence", 1.0),
                                source=TagSource(
                                    tag_dict.get("source", "auto")
                                ),
                            )
                        except (json.JSONDecodeError, KeyError, ValueError):
                            pass

        return result

    async def remove_tag(self, user_id: str, tag_name: str) -> bool:
        """
        移除用户标签

        Args:
            user_id: 用户ID
            tag_name: 标签名

        Returns:
            是否成功移除
        """
        key = self._get_tag_key(user_id)
        result = await self._redis.hdel(key, tag_name)

        if result > 0:
            # 从标签索引中移除
            await self._redis.srem(f"{self.TAG_INDEX_KEY}:{tag_name}", user_id)

            # 发布标签删除事件
            await self._redis.publish(
                "tag:deletes",
                json.dumps(
                    {
                        "user_id": user_id,
                        "tag_name": tag_name,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
            )

            logger.info(
                "Tag removed", user_id=user_id, tag_name=tag_name
            )
            return True

        return False

    async def get_users_by_tag(
        self,
        tag_name: str,
        tag_value: str | None = None,
    ) -> list[str]:
        """
        获取具有指定标签的用户列表

        Args:
            tag_name: 标签名
            tag_value: 标签值（可选，用于进一步筛选）

        Returns:
            用户ID列表
        """
        user_ids = await self._redis.smembers(f"{self.TAG_INDEX_KEY}:{tag_name}")

        if tag_value is None:
            return list(user_ids)

        # 需要进一步验证标签值
        result: list[str] = []
        for user_id in user_ids:
            tag = await self._redis.hget(self._get_tag_key(user_id), tag_name)
            if tag:
                try:
                    tag_dict = json.loads(tag)
                    if tag_dict.get("value") == tag_value:
                        result.append(user_id)
                except json.JSONDecodeError:
                    pass

        return result

    async def get_tag_statistics(self) -> dict[str, int]:
        """
        获取标签统计信息

        Returns:
            标签名 -> 用户数量的映射
        """
        # 扫描所有标签索引
        stats: dict[str, int] = {}
        cursor = 0
        pattern = f"{self.TAG_INDEX_KEY}:*"

        while True:
            cursor, keys = await self._redis.scan(
                cursor=cursor, match=pattern, count=100
            )
            for key in keys:
                tag_name = key.split(":")[-1]
                count = await self._redis.scard(key)
                stats[tag_name] = count

            if cursor == 0:
                break

        return stats
