"""
Agent Analytics E2E Integration Tests
"""
import pytest


class TestAgentAnalyticsE2E:
    """End-to-end tests for the agent analytics pipeline"""

    def test_full_agent_lifecycle(self, client):
        """Test complete agent lifecycle: create -> tag -> analyze -> compare"""
        agent_id = "e2e-test-agent"

        # Step 1: Create agent
        response = client.put(f"/api/agents/{agent_id}", json={
            "agent_name": "E2E Test Agent",
            "agent_type": "llm_agent",
            "model_name": "gpt-4",
        })
        assert response.status_code == 200

        # Step 2: Get agent profile
        response = client.get(f"/api/agents/{agent_id}")
        assert response.status_code == 200
        assert response.json()["agent_id"] == agent_id

        # Step 3: Add tags
        response = client.put(f"/api/agents/{agent_id}/tags", json={
            "tag_name": "environment",
            "tag_value": "test",
        })
        assert response.status_code == 200

        # Step 4: Get tags
        response = client.get(f"/api/agents/{agent_id}/tags")
        assert response.status_code == 200
        assert "environment" in response.json()["tags"]

        # Step 5: Get stats
        response = client.get(f"/api/agents/{agent_id}/stats")
        assert response.status_code == 200

        # Step 6: Risk assessment
        response = client.get(f"/api/agents/{agent_id}/risk")
        assert response.status_code == 200
        assert "risk_score" in response.json()

        # Step 7: Cleanup
        response = client.delete(f"/api/agents/{agent_id}")
        assert response.status_code == 200

    def test_agent_mock_to_insight_flow(self, client):
        """Test flow from mock event generation to insight analysis"""
        # Step 1: Generate events
        response = client.post("/api/agent-mock/generate", json={
            "agent_id": "flow-test-agent",
            "count": 5,
        })
        assert response.status_code == 200
        events = response.json()["events"]
        assert len(events) == 5

        # Step 2: Create agent profile from events
        agent_id = events[0]["agent_id"]
        client.put(f"/api/agents/{agent_id}", json={
            "agent_name": "Flow Test Agent",
            "agent_type": events[0]["agent_type"],
            "model_name": events[0].get("model_name"),
        })

        # Step 3: Verify agent exists
        response = client.get(f"/api/agents/{agent_id}")
        assert response.status_code == 200

    def test_scenario_generation_and_analysis(self, client):
        """Test scenario generation and basic analysis"""
        # Generate loop scenario
        response = client.post("/api/agent-mock/scenario/start", json={
            "scenario": "loop",
            "params": {"loop_count": 10},
        })
        assert response.status_code == 200
        assert response.json()["events_generated"] == 10

        # Generate cost explosion scenario
        response = client.post("/api/agent-mock/scenario/start", json={
            "scenario": "cost_explosion",
            "params": {"event_count": 5},
        })
        assert response.status_code == 200

        # List scenarios
        response = client.get("/api/agent-mock/scenarios")
        assert response.status_code == 200
        scenarios = response.json()["scenarios"]
        assert len(scenarios) >= 2

    def test_multiple_agents_comparison(self, client):
        """Test comparing multiple agents"""
        # Create agents
        for i in range(3):
            client.put(f"/api/agents/compare-agent-{i}", json={
                "agent_name": f"Agent {i}",
                "agent_type": "llm_agent",
            })

        # Compare
        response = client.post("/api/agents/compare", json={
            "agent_ids": ["compare-agent-0", "compare-agent-1", "compare-agent-2"],
            "metrics": ["success_rate"],
        })
        assert response.status_code == 200
        assert len(response.json()["agents"]) == 3

        # Cleanup
        for i in range(3):
            client.delete(f"/api/agents/compare-agent-{i}")

    def test_global_overview_with_agents(self, client):
        """Test global overview after creating agents"""
        # Create a few agents
        for i in range(3):
            client.put(f"/api/agents/overview-agent-{i}", json={
                "agent_name": f"Overview Agent {i}",
            })

        # Get overview
        response = client.get("/api/agents/stats/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["total_agents"] >= 3

        # Cleanup
        for i in range(3):
            client.delete(f"/api/agents/overview-agent-{i}")


@pytest.fixture
def client():
    """Create test client"""
    try:
        from behavior_mock.main import app
        from fastapi.testclient import TestClient
        return TestClient(app)
    except ImportError:
        pytest.skip("Mock app not available")
