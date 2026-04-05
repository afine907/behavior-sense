"""
Mock 服务 API 接口测试
"""
import pytest
from httpx import AsyncClient


class TestMockHealth:
    """Mock 服务健康检查测试"""

    @pytest.mark.asyncio
    async def test_health_check(self, mock_client: AsyncClient):
        """测试健康检查接口"""
        response = await mock_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "active_scenarios" in data
        assert "producer_connected" in data


class TestMockGenerator:
    """Mock 服务事件生成测试"""

    @pytest.mark.asyncio
    async def test_generate_events_default(self, mock_client: AsyncClient):
        """测试默认参数生成事件"""
        response = await mock_client.post(
            "/api/mock/generate",
            json={"count": 10}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["count"] == 10
        assert len(data["events"]) == 10
        assert "generated_at" in data

    @pytest.mark.asyncio
    async def test_generate_events_with_event_types(self, mock_client: AsyncClient):
        """测试指定事件类型生成"""
        response = await mock_client.post(
            "/api/mock/generate",
            json={
                "count": 5,
                "event_types": ["view", "click"],
                "weighted": False
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["count"] == 5
        for event in data["events"]:
            assert event["event_type"] in ["view", "click"]

    @pytest.mark.asyncio
    async def test_generate_events_weighted(self, mock_client: AsyncClient):
        """测试权重生成"""
        response = await mock_client.post(
            "/api/mock/generate",
            json={
                "count": 20,
                "user_pool_size": 100,
                "weighted": True
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["count"] == 20

    @pytest.mark.asyncio
    async def test_generate_events_invalid_type(self, mock_client: AsyncClient):
        """测试无效事件类型"""
        response = await mock_client.post(
            "/api/mock/generate",
            json={
                "count": 5,
                "event_types": ["invalid_type"]
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_generate_events_count_limit(self, mock_client: AsyncClient):
        """测试生成数量限制"""
        # 最大 10000
        response = await mock_client.post(
            "/api/mock/generate",
            json={"count": 10001}
        )

        assert response.status_code == 422  # Validation error


class TestMockScenario:
    """Mock 服务场景管理测试"""

    @pytest.mark.asyncio
    async def test_start_normal_scenario(self, mock_client: AsyncClient):
        """测试启动正常流量场景"""
        response = await mock_client.post(
            "/api/mock/scenario/start",
            json={
                "scenario_type": "normal",
                "duration_seconds": 2,  # 使用较短持续时间
                "rate_per_second": 5
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "scenario_id" in data
        assert data["status"] == "running"
        assert data["duration_seconds"] == 2

        # 清理：停止场景
        scenario_id = data["scenario_id"]
        await mock_client.post(f"/api/mock/scenario/{scenario_id}/stop")

    @pytest.mark.asyncio
    async def test_start_flash_sale_scenario(self, mock_client: AsyncClient):
        """测试启动秒杀场景"""
        response = await mock_client.post(
            "/api/mock/scenario/start",
            json={
                "scenario_type": "flash_sale",
                "duration_seconds": 2,  # 使用较短持续时间
                "peak_rate": 100,
                "product_id": "product_001"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "running"

        # 清理
        await mock_client.post(f"/api/mock/scenario/{data['scenario_id']}/stop")

    @pytest.mark.asyncio
    async def test_start_abnormal_scenario(self, mock_client: AsyncClient):
        """测试启动异常流量场景"""
        response = await mock_client.post(
            "/api/mock/scenario/start",
            json={
                "scenario_type": "abnormal",
                "duration_seconds": 2,  # 使用较短持续时间
                "attack_type": "brute_force",
                "malicious_user_ratio": 0.3,
                "rate_per_second": 50
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "running"

        # 清理
        await mock_client.post(f"/api/mock/scenario/{data['scenario_id']}/stop")

    @pytest.mark.asyncio
    async def test_start_gradual_scenario(self, mock_client: AsyncClient):
        """测试启动渐进负载场景"""
        response = await mock_client.post(
            "/api/mock/scenario/start",
            json={
                "scenario_type": "gradual",
                "duration_seconds": 2,  # 使用较短持续时间
                "start_rate": 10,
                "end_rate": 100
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "running"

        # 清理
        await mock_client.post(f"/api/mock/scenario/{data['scenario_id']}/stop")

    @pytest.mark.asyncio
    async def test_start_invalid_scenario_type(self, mock_client: AsyncClient):
        """测试无效场景类型"""
        response = await mock_client.post(
            "/api/mock/scenario/start",
            json={
                "scenario_type": "invalid_type",
                "duration_seconds": 10
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_scenarios(self, mock_client: AsyncClient):
        """测试列出场景"""
        response = await mock_client.get("/api/mock/scenarios")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_scenario_info(self, mock_client: AsyncClient, generate_rule_id: str):
        """测试获取场景信息"""
        # 使用唯一ID创建场景
        create_response = await mock_client.post(
            "/api/mock/scenario/start",
            json={
                "scenario_type": "normal",
                "scenario_id": f"test-info-{generate_rule_id}",  # 使用唯一ID
                "duration_seconds": 5,
                "rate_per_second": 5
            }
        )

        assert create_response.status_code == 200
        scenario_id = create_response.json()["scenario_id"]

        # 获取场景信息
        response = await mock_client.get(f"/api/mock/scenario/{scenario_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["scenario_id"] == scenario_id

        # 清理
        await mock_client.post(f"/api/mock/scenario/{scenario_id}/stop")

    @pytest.mark.asyncio
    async def test_get_nonexistent_scenario(self, mock_client: AsyncClient):
        """测试获取不存在的场景"""
        response = await mock_client.get("/api/mock/scenario/nonexistent_id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_stop_scenario(self, mock_client: AsyncClient, generate_rule_id: str):
        """测试停止场景"""
        # 使用唯一ID创建场景
        create_response = await mock_client.post(
            "/api/mock/scenario/start",
            json={
                "scenario_type": "normal",
                "scenario_id": f"test-stop-{generate_rule_id}",  # 使用唯一ID
                "duration_seconds": 10
            }
        )

        scenario_id = create_response.json()["scenario_id"]

        # 停止场景
        response = await mock_client.post(f"/api/mock/scenario/{scenario_id}/stop")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["final_status"] in ["stopped", "completed"]

    @pytest.mark.asyncio
    async def test_pause_and_resume_scenario(self, mock_client: AsyncClient, generate_rule_id: str):
        """测试暂停和恢复场景"""
        # 使用唯一ID创建场景
        create_response = await mock_client.post(
            "/api/mock/scenario/start",
            json={
                "scenario_type": "normal",
                "scenario_id": f"test-pause-{generate_rule_id}",  # 使用唯一ID
                "duration_seconds": 10
            }
        )

        scenario_id = create_response.json()["scenario_id"]

        # 暂停
        pause_response = await mock_client.post(
            f"/api/mock/scenario/{scenario_id}/pause"
        )
        assert pause_response.status_code == 200

        # 恢复
        resume_response = await mock_client.post(
            f"/api/mock/scenario/{scenario_id}/resume"
        )
        assert resume_response.status_code == 200

        # 清理
        await mock_client.post(f"/api/mock/scenario/{scenario_id}/stop")

    @pytest.mark.asyncio
    async def test_delete_scenario(self, mock_client: AsyncClient, generate_rule_id: str):
        """测试删除场景"""
        # 使用唯一ID创建场景
        create_response = await mock_client.post(
            "/api/mock/scenario/start",
            json={
                "scenario_type": "normal",
                "scenario_id": f"test-delete-{generate_rule_id}",  # 使用唯一ID
                "duration_seconds": 2
            }
        )

        scenario_id = create_response.json()["scenario_id"]

        # 先停止
        await mock_client.post(f"/api/mock/scenario/{scenario_id}/stop")

        # 删除
        response = await mock_client.delete(f"/api/mock/scenario/{scenario_id}")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_running_scenario(self, mock_client: AsyncClient, generate_rule_id: str):
        """测试删除运行中的场景（应该失败）"""
        # 使用唯一ID创建场景
        create_response = await mock_client.post(
            "/api/mock/scenario/start",
            json={
                "scenario_type": "normal",
                "scenario_id": f"test-delete-running-{generate_rule_id}",  # 使用唯一ID
                "duration_seconds": 60
            }
        )

        scenario_id = create_response.json()["scenario_id"]

        # 立即尝试直接删除（场景应该仍在运行）
        response = await mock_client.delete(f"/api/mock/scenario/{scenario_id}")

        # 应该返回 400（不能删除运行中的场景）
        assert response.status_code == 400

        # 清理
        await mock_client.post(f"/api/mock/scenario/{scenario_id}/stop")

    @pytest.mark.asyncio
    async def test_duplicate_scenario_id(self, mock_client: AsyncClient):
        """测试重复场景ID"""
        scenario_id = "test-duplicate-scenario"

        # 创建第一个，使用足够长的持续时间
        response1 = await mock_client.post(
            "/api/mock/scenario/start",
            json={
                "scenario_type": "normal",
                "scenario_id": scenario_id,
                "duration_seconds": 60  # 足够长确保场景仍在运行
            }
        )
        assert response1.status_code == 200

        # 立即尝试用相同ID创建
        response2 = await mock_client.post(
            "/api/mock/scenario/start",
            json={
                "scenario_type": "normal",
                "scenario_id": scenario_id,
                "duration_seconds": 60
            }
        )
        # 应该返回 400（场景已运行）
        assert response2.status_code == 400

        # 清理
        await mock_client.post(f"/api/mock/scenario/{scenario_id}/stop")
