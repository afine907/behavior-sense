"""
生产就绪端到端测试
"""
import pytest
import asyncio
from datetime import UTC, datetime


class TestProductionReadyE2E:
    """生产就绪端到端测试"""

    @pytest.mark.asyncio
    async def test_full_agent_lifecycle_with_db(self, client):
        """测试完整的Agent生命周期（使用数据库）"""
        agent_id = "prod-test-agent"

        # 1. 创建Agent
        response = await client.put(f"/api/agents/{agent_id}", json={
            "agent_name": "Production Test Agent",
            "agent_type": "llm_agent",
            "model_name": "gpt-4",
            "owner": "test-team",
        })
        assert response.status_code == 200

        # 2. 获取Agent
        response = await client.get(f"/api/agents/{agent_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent_id
        assert data["agent_name"] == "Production Test Agent"

        # 3. 设置标签
        response = await client.put(f"/api/agents/{agent_id}/tags", json={
            "tag_name": "environment",
            "tag_value": "production",
            "source": "MANUAL",
        })
        assert response.status_code == 200

        # 4. 获取标签
        response = await client.get(f"/api/agents/{agent_id}/tags")
        assert response.status_code == 200
        tags = response.json()["tags"]
        assert "environment" in tags
        assert tags["environment"]["value"] == "production"

        # 5. 更新统计
        response = await client.put(f"/api/agents/{agent_id}/stats", json={
            "total_events": 1000,
            "total_cost_usd": 45.50,
            "success_rate": 0.95,
        })
        assert response.status_code == 200

        # 6. 获取统计
        response = await client.get(f"/api/agents/{agent_id}/stats")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_events"] == 1000

        # 7. 风险评估
        response = await client.get(f"/api/agents/{agent_id}/risk")
        assert response.status_code == 200
        risk = response.json()
        assert "risk_score" in risk
        assert "risk_level" in risk

        # 8. 清理
        response = await client.delete(f"/api/agents/{agent_id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_agent_comparison_real_data(self, client):
        """测试Agent对比（真实数据）"""
        # 创建多个Agent
        agents = ["compare-a", "compare-b", "compare-c"]
        for agent_id in agents:
            await client.put(f"/api/agents/{agent_id}", json={
                "agent_name": f"Agent {agent_id}",
                "agent_type": "llm_agent",
            })

        # 对比
        response = await client.post("/api/agents/compare", json={
            "agent_ids": agents,
            "metrics": ["success_rate", "total_cost_usd"],
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["agents"]) == 3
        assert "metrics" in data

        # 清理
        for agent_id in agents:
            await client.delete(f"/api/agents/{agent_id}")

    @pytest.mark.asyncio
    async def test_global_overview_real_data(self, client):
        """测试全局概览（真实数据）"""
        # 创建Agent
        await client.put("/api/agents/overview-test", json={
            "agent_name": "Overview Test",
        })

        # 获取概览
        response = await client.get("/api/agents/stats/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_agents" in data
        assert data["total_agents"] >= 1

        # 清理
        await client.delete("/api/agents/overview-test")

    @pytest.mark.asyncio
    async def test_scenario_generation_and_query(self, client):
        """测试场景生成和查询"""
        # 生成场景
        response = await client.post("/api/agent-mock/scenario/start", json={
            "scenario": "normal",
            "duration_events": 50,
        })
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]

        # 查询场景
        response = await client.get(f"/api/agent-mock/scenarios/{scenario_id}")
        assert response.status_code == 200

        # 列出场景
        response = await client.get("/api/agent-mock/scenarios")
        assert response.status_code == 200
        assert len(response.json()["scenarios"]) >= 1

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """测试WebSocket连接"""
        from fastapi.testclient import TestClient
        from behavior_mock.main import app

        with TestClient(app) as client:
            with client.websocket_connect("/ws/agent-events") as websocket:
                data = websocket.receive_json()
                assert data["type"] == "connected"

                # 接收几个事件
                for _ in range(3):
                    event = websocket.receive_json()
                    assert event["type"] == "agent_event"
                    assert "data" in event


@pytest.fixture
async def client():
    """创建测试客户端"""
    from httpx import AsyncClient, ASGITransport
    from behavior_mock.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
