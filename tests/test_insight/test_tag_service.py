"""
behavior_insight 模块单元测试
"""
import pytest
from datetime import datetime
import json

from behavior_core.models.user import TagSource, TagValue
from behavior_insight.services.tag_service import TagService


class MockRedis:
    """模拟 Redis 客户端"""

    def __init__(self):
        self.data = {}
        self.sets = {}
        self.published = []

    async def hgetall(self, key: str) -> dict:
        return self.data.get(key, {})

    async def hset(self, key: str, field: str, value: str) -> int:
        if key not in self.data:
            self.data[key] = {}
        self.data[key][field] = value
        return 1

    async def hget(self, key: str, field: str) -> str | None:
        return self.data.get(key, {}).get(field)

    async def hdel(self, key: str, field: str) -> int:
        if key in self.data and field in self.data[key]:
            del self.data[key][field]
            return 1
        return 0

    async def sadd(self, key: str, *members) -> int:
        if key not in self.sets:
            self.sets[key] = set()
        before = len(self.sets[key])
        self.sets[key].update(members)
        return len(self.sets[key]) - before

    async def srem(self, key: str, *members) -> int:
        if key not in self.sets:
            return 0
        before = len(self.sets[key])
        self.sets[key].difference_update(members)
        return before - len(self.sets[key])

    async def smembers(self, key: str) -> set:
        return self.sets.get(key, set())

    async def scard(self, key: str) -> int:
        return len(self.sets.get(key, set()))

    async def publish(self, channel: str, message: str) -> int:
        self.published.append((channel, message))
        return 1

    async def scan(self, cursor: int = 0, match: str = None, count: int = 10):
        # 简化的 scan 实现
        keys = list(self.sets.keys())
        return 0, keys

    def pipeline(self):
        return MockPipeline(self)


class MockPipeline:
    """模拟 Redis Pipeline"""

    def __init__(self, redis: MockRedis):
        self._redis = redis
        self._commands = []

    def hget(self, key: str, field: str):
        self._commands.append(("hget", key, field))

    def hgetall(self, key: str):
        self._commands.append(("hgetall", key))

    async def execute(self):
        results = []
        for cmd in self._commands:
            if cmd[0] == "hget":
                results.append(self._redis.data.get(cmd[1], {}).get(cmd[2]))
            elif cmd[0] == "hgetall":
                results.append(self._redis.data.get(cmd[1], {}))
        return results

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class TestTagService:
    """标签服务测试"""

    @pytest.fixture
    def mock_redis(self):
        return MockRedis()

    @pytest.fixture
    def tag_service(self, mock_redis):
        return TagService(mock_redis)

    @pytest.mark.asyncio
    async def test_update_tag(self, tag_service, mock_redis):
        """测试更新标签"""
        result = await tag_service.update_tag(
            user_id="user_001",
            tag_name="level",
            value="vip",
            source=TagSource.RULE,
        )

        assert result.value == "vip"
        assert result.source == TagSource.RULE

        # 验证 Redis 存储
        key = "user:tags:user_001"
        assert key in mock_redis.data
        assert "level" in mock_redis.data[key]

    @pytest.mark.asyncio
    async def test_get_user_tags(self, tag_service, mock_redis):
        """测试获取用户标签"""
        # 先添加标签
        await tag_service.update_tag("user_001", "level", "vip")
        await tag_service.update_tag("user_001", "risk", "high")

        # 获取标签
        user_tags = await tag_service.get_user_tags("user_001")

        assert user_tags is not None
        assert user_tags.user_id == "user_001"
        assert len(user_tags.tags) == 2

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_tags(self, tag_service):
        """测试获取不存在用户的标签"""
        user_tags = await tag_service.get_user_tags("nonexistent_user")
        assert user_tags is None

    @pytest.mark.asyncio
    async def test_remove_tag(self, tag_service, mock_redis):
        """测试移除标签"""
        # 先添加标签
        await tag_service.update_tag("user_001", "level", "vip")

        # 移除标签
        result = await tag_service.remove_tag("user_001", "level")
        assert result is True

        # 验证标签已移除
        user_tags = await tag_service.get_user_tags("user_001")
        assert user_tags is None or "level" not in user_tags.tags

    @pytest.mark.asyncio
    async def test_remove_nonexistent_tag(self, tag_service):
        """测试移除不存在的标签"""
        result = await tag_service.remove_tag("user_001", "nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_batch_get_tags(self, tag_service):
        """测试批量获取标签"""
        # 添加多个用户的标签
        await tag_service.update_tag("user_001", "level", "vip")
        await tag_service.update_tag("user_002", "level", "normal")

        # 批量获取
        results = await tag_service.batch_get_tags(
            user_ids=["user_001", "user_002"],
            tag_names=["level"]
        )

        assert "user_001" in results
        assert "user_002" in results

    @pytest.mark.asyncio
    async def test_get_users_by_tag(self, tag_service):
        """测试根据标签获取用户列表"""
        # 添加标签
        await tag_service.update_tag("user_001", "level", "vip")
        await tag_service.update_tag("user_002", "level", "vip")
        await tag_service.update_tag("user_003", "level", "normal")

        # 获取所有 level=vip 的用户
        users = await tag_service.get_users_by_tag("level", "vip")

        assert "user_001" in users
        assert "user_002" in users
        assert "user_003" not in users

    @pytest.mark.asyncio
    async def test_tag_with_confidence(self, tag_service):
        """测试带置信度的标签"""
        await tag_service.update_tag(
            user_id="user_001",
            tag_name="churn_risk",
            value="high",
            confidence=0.85,
        )

        user_tags = await tag_service.get_user_tags("user_001")
        assert user_tags.tags["churn_risk"].confidence == 0.85

    @pytest.mark.asyncio
    async def test_tag_expiry(self, tag_service):
        """测试标签过期时间"""
        expire_at = datetime(2024, 12, 31, 23, 59, 59)
        await tag_service.update_tag(
            user_id="user_001",
            tag_name="promo",
            value="eligible",
            expire_at=expire_at,
        )

        user_tags = await tag_service.get_user_tags("user_001")
        assert user_tags.tags["promo"].expire_at == expire_at

    @pytest.mark.asyncio
    async def test_tag_statistics(self, tag_service):
        """测试标签统计"""
        await tag_service.update_tag("user_001", "level", "vip")
        await tag_service.update_tag("user_002", "level", "normal")
        await tag_service.update_tag("user_003", "risk", "high")

        stats = await tag_service.get_tag_statistics()

        assert "level" in stats
        assert "risk" in stats
