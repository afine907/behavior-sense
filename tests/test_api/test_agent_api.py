"""
Agent API Integration Tests

Tests for agent mock, agent insight, and agent trace API endpoints.
"""

import uuid
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# ============================================================
# Local fixtures for apps not covered by conftest.py
# ============================================================


@pytest_asyncio.fixture
async def agent_mock_client() -> AsyncClient:
    """Agent mock service test client"""
    from behavior_mock.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def agent_insight_client() -> AsyncClient:
    """Agent insight service test client"""
    from behavior_insight.main import app
    from behavior_insight.repositories.user_repo import UserRepository
    from behavior_insight.services.tag_service import TagService

    from tests.test_api.conftest import MockRedis

    mock_redis_instance = MockRedis()

    app.state.redis = mock_redis_instance

    @asynccontextmanager
    async def mock_async_session_factory():
        yield None

    app.state.async_session_factory = mock_async_session_factory
    app.state.tag_service = TagService(mock_redis_instance)
    app.state.user_repo = UserRepository(None)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def agent_trace_client() -> AsyncClient:
    """Agent trace service test client"""
    from behavior_logs.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def unique_id() -> str:
    """Generate a unique ID for test isolation"""
    return uuid.uuid4().hex[:8]


# ============================================================
# Agent Mock API Tests
# ============================================================


class TestAgentMockAPI:
    """Tests for agent mock API endpoints"""

    @pytest.mark.asyncio
    async def test_health(self, agent_mock_client: AsyncClient):
        """Test agent mock health endpoint"""
        response = await agent_mock_client.get("/api/agent-mock/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "agent-mock"
        assert "active_scenarios" in data

    @pytest.mark.asyncio
    async def test_list_agents(self, agent_mock_client: AsyncClient):
        """Test listing available agent profiles"""
        response = await agent_mock_client.get("/api/agent-mock/agents")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) > 0

        # Verify agent profile structure
        agent = data["agents"][0]
        assert "agent_id" in agent
        assert "agent_type" in agent
        assert "model" in agent
        assert "tools" in agent
        assert "behavior" in agent

    @pytest.mark.asyncio
    async def test_generate_events(self, agent_mock_client: AsyncClient):
        """Test generating agent events"""
        response = await agent_mock_client.post(
            "/api/agent-mock/generate",
            json={"count": 5, "agent_type": "llm_agent"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["count"] == 5
        assert len(data["events"]) == 5

        # Verify event structure
        event = data["events"][0]
        assert "event_id" in event
        assert "agent_id" in event
        assert "agent_type" in event
        assert "event_type" in event
        assert "timestamp" in event
        assert "trace_id" in event
        assert "session_id" in event

    @pytest.mark.asyncio
    async def test_generate_events_with_specific_agent(self, agent_mock_client: AsyncClient):
        """Test generating events for a specific agent"""
        response = await agent_mock_client.post(
            "/api/agent-mock/generate",
            json={
                "agent_id": "test-agent-001",
                "count": 3,
                "model_name": "gpt-4",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        for event in data["events"]:
            assert event["agent_id"] == "test-agent-001"

    @pytest.mark.asyncio
    async def test_generate_events_with_event_types(self, agent_mock_client: AsyncClient):
        """Test generating events with specific event type filters"""
        response = await agent_mock_client.post(
            "/api/agent-mock/generate",
            json={
                "count": 5,
                "event_types": ["tool_call"],
                "include_tools": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5

    @pytest.mark.asyncio
    async def test_generate_events_count_limit(self, agent_mock_client: AsyncClient):
        """Test that generating too many events returns validation error"""
        response = await agent_mock_client.post(
            "/api/agent-mock/generate",
            json={"count": 1001},
        )

        assert response.status_code == 422  # Pydantic validation error

    @pytest.mark.asyncio
    async def test_start_scenario_normal(self, agent_mock_client: AsyncClient):
        """Test starting a normal scenario"""
        response = await agent_mock_client.post(
            "/api/agent-mock/scenario/start",
            json={
                "scenario": "normal",
                "duration_events": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["events_generated"] == 10
        assert data["scenario_type"] == "normal"
        assert "scenario_id" in data

    @pytest.mark.asyncio
    async def test_start_scenario_loop(self, agent_mock_client: AsyncClient):
        """Test starting a loop detection scenario"""
        response = await agent_mock_client.post(
            "/api/agent-mock/scenario/start",
            json={
                "scenario": "loop",
                "params": {"loop_count": 15},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["events_generated"] == 15

    @pytest.mark.asyncio
    async def test_start_scenario_cost_explosion(self, agent_mock_client: AsyncClient):
        """Test starting a cost explosion scenario"""
        response = await agent_mock_client.post(
            "/api/agent-mock/scenario/start",
            json={
                "scenario": "cost_explosion",
                "params": {"event_count": 10},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["events_generated"] == 10

    @pytest.mark.asyncio
    async def test_start_scenario_cascading_failure(self, agent_mock_client: AsyncClient):
        """Test starting a cascading failure scenario"""
        response = await agent_mock_client.post(
            "/api/agent-mock/scenario/start",
            json={
                "scenario": "cascading_failure",
                "params": {"event_count": 20},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["events_generated"] > 0

    @pytest.mark.asyncio
    async def test_start_invalid_scenario(self, agent_mock_client: AsyncClient):
        """Test starting an invalid scenario returns 400"""
        response = await agent_mock_client.post(
            "/api/agent-mock/scenario/start",
            json={"scenario": "nonexistent"},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_scenarios(self, agent_mock_client: AsyncClient):
        """Test listing scenarios after creating one"""
        # First create a scenario
        await agent_mock_client.post(
            "/api/agent-mock/scenario/start",
            json={"scenario": "normal", "duration_events": 5},
        )

        response = await agent_mock_client.get("/api/agent-mock/scenarios")

        assert response.status_code == 200
        data = response.json()
        assert "scenarios" in data
        assert len(data["scenarios"]) > 0

        # Verify scenario structure
        scenario = data["scenarios"][0]
        assert "scenario_id" in scenario
        assert "scenario_type" in scenario
        assert "status" in scenario
        assert "events_generated" in scenario

    @pytest.mark.asyncio
    async def test_get_scenario_details(self, agent_mock_client: AsyncClient):
        """Test getting scenario details by ID"""
        # Create a scenario
        create_response = await agent_mock_client.post(
            "/api/agent-mock/scenario/start",
            json={"scenario": "normal", "duration_events": 5},
        )
        scenario_id = create_response.json()["scenario_id"]

        # Get scenario details
        response = await agent_mock_client.get(f"/api/agent-mock/scenarios/{scenario_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["scenario_id"] == scenario_id
        assert data["scenario_type"] == "normal"
        assert data["events_generated"] == 5

    @pytest.mark.asyncio
    async def test_delete_scenario(self, agent_mock_client: AsyncClient):
        """Test deleting a completed scenario"""
        # Create a scenario
        create_response = await agent_mock_client.post(
            "/api/agent-mock/scenario/start",
            json={"scenario": "normal", "duration_events": 5},
        )
        scenario_id = create_response.json()["scenario_id"]

        # Delete scenario
        response = await agent_mock_client.delete(f"/api/agent-mock/scenarios/{scenario_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        # Verify it's gone
        get_response = await agent_mock_client.get(f"/api/agent-mock/scenarios/{scenario_id}")
        assert get_response.status_code == 404


# ============================================================
# Agent Insight API Tests
# ============================================================


class TestAgentInsightAPI:
    """Tests for agent insight API endpoints"""

    @pytest.mark.asyncio
    async def test_list_agents_empty(self, agent_insight_client: AsyncClient):
        """Test listing agents when none exist"""
        response = await agent_insight_client.get("/api/agents")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["agents"] == []
        assert data["page"] == 1
        assert data["page_size"] == 20

    @pytest.mark.asyncio
    async def test_create_and_get_agent(self, agent_insight_client: AsyncClient, unique_id: str):
        """Test creating and retrieving an agent profile"""
        agent_id = f"test-agent-{unique_id}"

        # Create agent
        create_response = await agent_insight_client.put(
            f"/api/agents/{agent_id}",
            json={
                "agent_name": "Test Agent",
                "agent_type": "llm_agent",
                "model_name": "gpt-4",
            },
        )
        assert create_response.status_code == 200
        assert create_response.json()["status"] == "ok"

        # Get agent
        get_response = await agent_insight_client.get(f"/api/agents/{agent_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["agent_id"] == agent_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self, agent_insight_client: AsyncClient):
        """Test getting a nonexistent agent returns 404"""
        response = await agent_insight_client.get("/api/agents/nonexistent-agent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_agents_after_create(
        self, agent_insight_client: AsyncClient, unique_id: str
    ):
        """Test listing agents after creating one"""
        agent_id = f"test-list-{unique_id}"

        # Create agent
        await agent_insight_client.put(
            f"/api/agents/{agent_id}",
            json={"agent_name": "List Test Agent"},
        )

        # List agents
        response = await agent_insight_client.get("/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(a["agent_id"] == agent_id for a in data["agents"])

    @pytest.mark.asyncio
    async def test_update_agent_profile(self, agent_insight_client: AsyncClient, unique_id: str):
        """Test updating an existing agent profile"""
        agent_id = f"test-update-{unique_id}"

        # Create agent
        await agent_insight_client.put(
            f"/api/agents/{agent_id}",
            json={"agent_name": "Original Name"},
        )

        # Update agent
        update_response = await agent_insight_client.put(
            f"/api/agents/{agent_id}",
            json={"agent_name": "Updated Name", "model_name": "claude-3-opus"},
        )
        assert update_response.status_code == 200

        # Verify update
        get_response = await agent_insight_client.get(f"/api/agents/{agent_id}")
        assert get_response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_agent(self, agent_insight_client: AsyncClient, unique_id: str):
        """Test deleting an agent"""
        agent_id = f"test-delete-{unique_id}"

        # Create agent
        await agent_insight_client.put(
            f"/api/agents/{agent_id}",
            json={"agent_name": "Delete Test"},
        )

        # Delete agent
        delete_response = await agent_insight_client.delete(f"/api/agents/{agent_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["status"] == "ok"

        # Verify deletion
        get_response = await agent_insight_client.get(f"/api/agents/{agent_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_agent_tags(self, agent_insight_client: AsyncClient, unique_id: str):
        """Test agent tag operations"""
        agent_id = f"test-tags-{unique_id}"

        # Create agent
        await agent_insight_client.put(
            f"/api/agents/{agent_id}",
            json={"agent_name": "Tag Test"},
        )

        # Add tag
        put_response = await agent_insight_client.put(
            f"/api/agents/{agent_id}/tags",
            json={
                "tag_name": "risk_level",
                "tag_value": "high",
                "source": "RULE",
            },
        )
        assert put_response.status_code == 200
        assert put_response.json()["tag"] == "risk_level"

        # Get tags
        get_response = await agent_insight_client.get(f"/api/agents/{agent_id}/tags")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["agent_id"] == agent_id
        assert "risk_level" in data["tags"]
        assert data["tags"]["risk_level"]["value"] == "high"
        assert data["tags"]["risk_level"]["source"] == "RULE"

    @pytest.mark.asyncio
    async def test_delete_agent_tag(self, agent_insight_client: AsyncClient, unique_id: str):
        """Test deleting an agent tag"""
        agent_id = f"test-tag-del-{unique_id}"

        # Create agent and add tag
        await agent_insight_client.put(
            f"/api/agents/{agent_id}",
            json={"agent_name": "Tag Delete Test"},
        )
        await agent_insight_client.put(
            f"/api/agents/{agent_id}/tags",
            json={"tag_name": "temp_tag", "tag_value": "value"},
        )

        # Delete tag
        delete_response = await agent_insight_client.delete(f"/api/agents/{agent_id}/tags/temp_tag")
        assert delete_response.status_code == 200

        # Verify tag is gone
        get_response = await agent_insight_client.get(f"/api/agents/{agent_id}/tags")
        assert "temp_tag" not in get_response.json()["tags"]

    @pytest.mark.asyncio
    async def test_agent_stats(self, agent_insight_client: AsyncClient):
        """Test getting agent statistics"""
        response = await agent_insight_client.get("/api/agents/test-agent/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "test-agent"
        assert "total_events" in data
        assert "total_tokens" in data
        assert "total_cost_usd" in data
        assert "success_rate" in data

    @pytest.mark.asyncio
    async def test_agent_cost_breakdown(self, agent_insight_client: AsyncClient):
        """Test getting agent cost breakdown"""
        response = await agent_insight_client.get("/api/agents/test-agent/stats/cost")

        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert "total_cost_usd" in data
        assert "cost_by_model" in data
        assert "cost_by_tool" in data

    @pytest.mark.asyncio
    async def test_agent_performance(self, agent_insight_client: AsyncClient):
        """Test getting agent performance metrics"""
        response = await agent_insight_client.get("/api/agents/test-agent/stats/performance")

        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert "avg_latency_ms" in data
        assert "success_rate" in data
        assert "error_rate" in data

    @pytest.mark.asyncio
    async def test_agent_risk_assessment(self, agent_insight_client: AsyncClient):
        """Test agent risk assessment"""
        response = await agent_insight_client.get("/api/agents/test-agent/risk")

        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert "risk_score" in data
        assert "risk_level" in data
        assert "risk_factors" in data
        assert data["risk_level"] in ("low", "medium", "high", "critical")

    @pytest.mark.asyncio
    async def test_agents_overview(self, agent_insight_client: AsyncClient):
        """Test global agents overview"""
        response = await agent_insight_client.get("/api/agents/stats/overview")

        assert response.status_code == 200
        data = response.json()
        assert "total_agents" in data
        assert "active_agents" in data
        assert "total_cost_usd" in data
        assert "total_events" in data
        assert "total_tokens" in data
        assert "avg_success_rate" in data

    @pytest.mark.asyncio
    async def test_cost_summary(self, agent_insight_client: AsyncClient):
        """Test global cost summary"""
        response = await agent_insight_client.get("/api/agents/stats/cost")

        assert response.status_code == 200
        data = response.json()
        assert "total_cost_usd" in data
        assert "by_agent" in data
        assert "by_model" in data

    @pytest.mark.asyncio
    async def test_compare_agents(self, agent_insight_client: AsyncClient):
        """Test agent comparison"""
        response = await agent_insight_client.post(
            "/api/agents/compare",
            json={
                "agent_ids": ["agent-1", "agent-2"],
                "metrics": ["success_rate", "avg_latency"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "rankings" in data
        assert "insights" in data
        assert "agents" in data
        assert set(data["agents"]) == {"agent-1", "agent-2"}

    @pytest.mark.asyncio
    async def test_agent_capabilities(self, agent_insight_client: AsyncClient, unique_id: str):
        """Test getting agent capabilities"""
        agent_id = f"test-caps-{unique_id}"

        # Create agent with capabilities
        await agent_insight_client.put(
            f"/api/agents/{agent_id}",
            json={
                "agent_name": "Cap Test",
                "capabilities": ["code_generation", "analysis"],
                "supported_tools": ["code_execution", "calculator"],
            },
        )

        response = await agent_insight_client.get(f"/api/agents/{agent_id}/capabilities")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent_id
        assert "capabilities" in data
        assert "supported_tools" in data

    @pytest.mark.asyncio
    async def test_agents_by_tag(self, agent_insight_client: AsyncClient, unique_id: str):
        """Test finding agents by tag"""
        agent_id = f"test-tag-search-{unique_id}"

        # Create agent and add a tag
        await agent_insight_client.put(
            f"/api/agents/{agent_id}",
            json={"agent_name": "Tag Search Test"},
        )
        await agent_insight_client.put(
            f"/api/agents/{agent_id}/tags",
            json={"tag_name": "environment", "tag_value": "production"},
        )

        # Search by tag
        response = await agent_insight_client.get(
            "/api/agents/tags/by-value",
            params={"tag_name": "environment", "tag_value": "production"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(a["agent_id"] == agent_id for a in data["agents"])

    @pytest.mark.asyncio
    async def test_list_agents_with_pagination(self, agent_insight_client: AsyncClient):
        """Test agent listing with pagination parameters"""
        response = await agent_insight_client.get(
            "/api/agents",
            params={"page": 1, "page_size": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["agents"]) <= 5


# ============================================================
# Agent Trace API Tests
# ============================================================


class TestAgentTraceAPI:
    """Tests for agent trace API endpoints"""

    @pytest.mark.asyncio
    async def test_list_traces_empty(self, agent_trace_client: AsyncClient):
        """Test listing traces when none exist"""
        response = await agent_trace_client.get("/api/traces")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["traces"] == []
        assert data["page"] == 1
        assert data["page_size"] == 20

    @pytest.mark.asyncio
    async def test_trace_stats_empty(self, agent_trace_client: AsyncClient):
        """Test trace statistics with no traces"""
        response = await agent_trace_client.get("/api/traces/stats/overview")

        assert response.status_code == 200
        data = response.json()
        assert data["total_traces"] == 0
        assert data["total_spans"] == 0
        assert data["error_traces"] == 0
        assert data["error_rate"] == 0

    @pytest.mark.asyncio
    async def test_get_nonexistent_trace(self, agent_trace_client: AsyncClient):
        """Test getting a nonexistent trace returns 404"""
        response = await agent_trace_client.get("/api/traces/nonexistent-trace-id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_nonexistent_trace_spans(self, agent_trace_client: AsyncClient):
        """Test getting spans for a nonexistent trace returns 404"""
        response = await agent_trace_client.get("/api/traces/nonexistent-trace-id/spans")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_nonexistent_trace_waterfall(self, agent_trace_client: AsyncClient):
        """Test getting waterfall for a nonexistent trace returns 404"""
        response = await agent_trace_client.get("/api/traces/nonexistent-trace-id/waterfall")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_nonexistent_trace_timeline(self, agent_trace_client: AsyncClient):
        """Test getting timeline for a nonexistent trace returns 404"""
        response = await agent_trace_client.get("/api/traces/nonexistent-trace-id/timeline")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_nonexistent_trace_errors(self, agent_trace_client: AsyncClient):
        """Test getting errors for a nonexistent trace returns 404"""
        response = await agent_trace_client.get("/api/traces/nonexistent-trace-id/errors")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_traces_with_filters(self, agent_trace_client: AsyncClient):
        """Test listing traces with query filters"""
        response = await agent_trace_client.get(
            "/api/traces",
            params={
                "agent_id": "agent-001",
                "page": 1,
                "page_size": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10
