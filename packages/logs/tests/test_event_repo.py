"""
EventLogRepository 单元测试
"""
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from behavior_core.models.event import EventType, UserBehavior
from behavior_logs.repositories.event_repo import (
    EventLogQuery,
    EventLogRepository,
)


@pytest.fixture
def mock_client():
    """Mock ClickHouse client"""
    client = MagicMock()
    return client


@pytest.fixture
def repo(mock_client):
    """Create repository with mocked client"""
    return EventLogRepository(client=mock_client)


class TestEventLogRepository:
    """EventLogRepository 测试"""

    def test_order_direction_whitelist(self, repo):
        """测试 ORDER BY 方向白名单"""
        # Valid directions - these should be accepted
        query_desc = EventLogQuery(sort_order="desc")
        assert query_desc.sort_order == "desc"

        query_asc = EventLogQuery(sort_order="asc")
        assert query_asc.sort_order == "asc"

    @pytest.mark.asyncio
    async def test_insert_events_empty(self, repo):
        """测试插入空事件列表"""
        await repo.insert_events([])
        repo._client.insert.assert_not_called()

    @pytest.mark.asyncio
    async def test_insert_events_single(self, repo):
        """测试插入单个事件"""
        event = UserBehavior(
            event_id="test-001",
            user_id="user_001",
            event_type=EventType.VIEW,
            timestamp=datetime.now(UTC),
            session_id="session_001",
            page_url="/test",
            properties={"key": "value"},
        )

        await repo.insert_events([event])

        repo._client.insert.assert_called_once()
        call_args = repo._client.insert.call_args
        # call_args[0] is positional args, [1] is keyword args
        assert call_args[0][0] == "event_logs"
        assert len(call_args[0][1]) == 1  # rows is second positional arg

    @pytest.mark.asyncio
    async def test_insert_events_batch(self, repo):
        """测试批量插入事件"""
        events = [
            UserBehavior(
                event_id=f"test-{i}",
                user_id=f"user_{i}",
                event_type=EventType.CLICK,
                timestamp=datetime.now(UTC),
            )
            for i in range(10)
        ]

        await repo.insert_events(events)

        repo._client.insert.assert_called_once()
        call_args = repo._client.insert.call_args
        assert len(call_args[0][1]) == 10  # rows is second positional arg

    @pytest.mark.asyncio
    async def test_query_events_empty_result(self, repo):
        """测试查询空结果"""
        repo._client.query.return_value.first_item = {"total": 0}
        repo._client.query.return_value.result_rows = []

        query = EventLogQuery()
        items, total = await repo.query_events(query)

        assert total == 0
        assert items == []

    @pytest.mark.asyncio
    async def test_query_events_with_filters(self, repo):
        """测试带过滤条件的查询"""
        repo._client.query.return_value.first_item = {"total": 1}
        repo._client.query.return_value.result_rows = [
            [
                "event-001",
                "user_001",
                "view",
                datetime.now(UTC),
                "session_001",
                "/test",
                None,
                None,
                None,
                "{}",
                None,
            ]
        ]

        query = EventLogQuery(
            user_id="user_001",
            event_type="view",
        )
        items, total = await repo.query_events(query)

        assert total == 1
        assert len(items) == 1
        assert items[0].user_id == "user_001"
        assert items[0].event_type == "view"

    @pytest.mark.asyncio
    async def test_get_event_by_id_found(self, repo):
        """测试根据 ID 获取事件 - 找到"""
        repo._client.query.return_value.result_rows = [
            [
                "event-001",
                "user_001",
                "view",
                datetime.now(UTC),
                "session_001",
                "/test",
                None,
                None,
                None,
                '{"key": "value"}',
                None,
            ]
        ]

        event = await repo.get_event_by_id("event-001")

        assert event is not None
        assert event.event_id == "event-001"
        assert event.properties == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_event_by_id_not_found(self, repo):
        """测试根据 ID 获取事件 - 未找到"""
        repo._client.query.return_value.result_rows = []

        event = await repo.get_event_by_id("nonexistent")

        assert event is None

    @pytest.mark.asyncio
    async def test_get_stats(self, repo):
        """测试获取统计"""
        repo._client.query.side_effect = [
            MagicMock(result_rows=[("view", 100), ("click", 50)]),
            MagicMock(first_item={
                "total_events": 150,
                "unique_users": 30,
                "unique_sessions": 45,
            }),
        ]

        stats = await repo.get_stats()

        assert stats.total_events == 150
        assert stats.unique_users == 30
        assert stats.unique_sessions == 45
        assert stats.event_type_counts == {"view": 100, "click": 50}

    def test_close(self, repo):
        """测试关闭连接"""
        repo.close()
        repo._client.close.assert_called_once()


class TestEventLogQuery:
    """EventLogQuery 测试"""

    def test_default_values(self):
        """测试默认值"""
        query = EventLogQuery()
        assert query.page == 1
        assert query.size == 50
        assert query.sort_order == "desc"

    def test_validation_page_ge1(self):
        """测试页码验证"""
        with pytest.raises(ValueError):
            EventLogQuery(page=0)

    def test_validation_size_range(self):
        """测试分页大小范围"""
        with pytest.raises(ValueError):
            EventLogQuery(size=0)

        with pytest.raises(ValueError):
            EventLogQuery(size=300)
