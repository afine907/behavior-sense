"""
SDK客户端测试
"""
import pytest
from unittest.mock import AsyncMock, patch
from behavior_sdk.client import BehaviorSenseClient
from behavior_sdk.models import AgentEvent, AgentProfile, TokenUsage


class TestBehaviorSenseClient:
    """SDK客户端测试"""

    @pytest.fixture
    def client(self):
        return BehaviorSenseClient(base_url="http://test:8001")

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """测试上下文管理器"""
        async with BehaviorSenseClient(base_url="http://test:8001") as client:
            assert client is not None

    @pytest.mark.asyncio
    async def test_track_event(self, client):
        """测试发送事件"""
        event = AgentEvent(
            agent_id="test-agent",
            event_type="tool_call",
        )
        # Mock the HTTP call
        with patch.object(client, '_get_client') as mock_get:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.raise_for_status = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get.return_value = mock_client

            result = await client.track_event(event)
            assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_get_agent(self, client):
        """测试获取Agent"""
        with patch.object(client, '_get_client') as mock_get:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "agent_id": "test-agent",
                "agent_name": "Test Agent",
                "status": "active",
            }
            mock_response.raise_for_status = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_get.return_value = mock_client

            agent = await client.get_agent("test-agent")
            assert agent.agent_id == "test-agent"

    @pytest.mark.asyncio
    async def test_create_agent(self, client):
        """测试创建Agent"""
        agent = AgentProfile(
            agent_id="new-agent",
            agent_name="New Agent",
        )
        with patch.object(client, '_get_client') as mock_get:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = agent.model_dump()
            mock_response.raise_for_status = AsyncMock()
            mock_client.put.return_value = mock_response
            mock_get.return_value = mock_client

            result = await client.create_agent(agent)
            assert result.agent_id == "new-agent"


class TestSDKModels:
    """SDK模型测试"""

    def test_agent_event_creation(self):
        """测试创建AgentEvent"""
        event = AgentEvent(
            agent_id="test-agent",
            event_type="tool_call",
            tool_call={"tool_name": "search", "latency_ms": 100},
        )
        assert event.agent_id == "test-agent"
        assert event.event_type == "tool_call"

    def test_agent_event_with_token_usage(self):
        """测试带Token使用的AgentEvent"""
        event = AgentEvent(
            agent_id="test-agent",
            event_type="llm_request",
            token_usage=TokenUsage(
                prompt_tokens=1000,
                completion_tokens=500,
            ),
        )
        assert event.token_usage.prompt_tokens == 1000

    def test_agent_profile_creation(self):
        """测试创建AgentProfile"""
        profile = AgentProfile(
            agent_id="test-agent",
            agent_name="Test Agent",
            agent_type="llm_agent",
            model_name="gpt-4",
        )
        assert profile.agent_id == "test-agent"
        assert profile.status == "active"
