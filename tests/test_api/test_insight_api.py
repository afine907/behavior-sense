"""
Insight 服务 API 接口测试
"""
import pytest
from httpx import AsyncClient


class TestInsightHealth:
    """Insight 服务健康检查测试"""

    @pytest.mark.asyncio
    async def test_health_check(self, insight_client: AsyncClient):
        """测试健康检查接口"""
        response = await insight_client.get("/health")

        # 注意：可能因为 Redis/DB 连接失败返回 degraded
        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["service"] == "insight"
        assert "redis" in data
        assert "database" in data

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, insight_client: AsyncClient):
        """测试 Prometheus 指标接口"""
        response = await insight_client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_root_endpoint(self, insight_client: AsyncClient):
        """测试根路径"""
        response = await insight_client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "BehaviorSense Insight"
        assert "version" in data
        assert data["docs"] == "/docs"


class TestInsightTags:
    """Insight 服务标签管理测试"""

    @pytest.mark.asyncio
    async def test_update_user_tag(self, insight_client: AsyncClient, generate_user_id: str):
        """测试更新用户标签"""
        response = await insight_client.put(
            f"/api/insight/user/{generate_user_id}/tag",
            json={
                "tag_name": "level",
                "tag_value": "vip",
                "source": "MANUAL",
                "confidence": 1.0
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["user_id"] == generate_user_id
        assert data["tag_name"] == "level"

    @pytest.mark.asyncio
    async def test_get_user_tags(self, insight_client: AsyncClient, generate_user_id: str):
        """测试获取用户标签"""
        # 先更新标签
        await insight_client.put(
            f"/api/insight/user/{generate_user_id}/tag",
            json={
                "tag_name": "level",
                "tag_value": "vip"
            }
        )

        # 获取标签
        response = await insight_client.get(f"/api/insight/user/{generate_user_id}/tags")

        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == generate_user_id
        assert "tags" in data

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_tags(self, insight_client: AsyncClient):
        """测试获取不存在用户的标签"""
        response = await insight_client.get("/api/insight/user/nonexistent_user/tags")

        # 可能返回 404 或空标签
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_delete_user_tag(self, insight_client: AsyncClient, generate_user_id: str):
        """测试删除用户标签"""
        # 先创建标签
        await insight_client.put(
            f"/api/insight/user/{generate_user_id}/tag",
            json={"tag_name": "temp", "tag_value": "test"}
        )

        # 删除标签
        response = await insight_client.delete(
            f"/api/insight/user/{generate_user_id}/tag/temp"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["removed"] is True

    @pytest.mark.asyncio
    async def test_delete_nonexistent_tag(self, insight_client: AsyncClient, generate_user_id: str):
        """测试删除不存在的标签"""
        response = await insight_client.delete(
            f"/api/insight/user/{generate_user_id}/tag/nonexistent_tag"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_batch_get_tags(self, insight_client: AsyncClient):
        """测试批量获取标签"""
        user_ids = ["user_1", "user_2", "user_3"]

        # 先为用户创建标签
        for user_id in user_ids:
            await insight_client.put(
                f"/api/insight/user/{user_id}/tag",
                json={"tag_name": "level", "tag_value": "normal"}
            )

        # 批量获取
        response = await insight_client.post(
            "/api/insight/user/tags/batch",
            json={
                "user_ids": user_ids,
                "tag_names": ["level"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "results" in data

    @pytest.mark.asyncio
    async def test_batch_get_tags_too_many_users(self, insight_client: AsyncClient):
        """测试批量获取超过限制"""
        user_ids = [f"user_{i}" for i in range(101)]

        response = await insight_client.post(
            "/api/insight/user/tags/batch",
            json={"user_ids": user_ids}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_users_by_tag(self, insight_client: AsyncClient):
        """测试根据标签获取用户"""
        # 创建标签
        await insight_client.put(
            "/api/insight/user/user_001/tag",
            json={"tag_name": "vip_status", "tag_value": "gold"}
        )
        await insight_client.put(
            "/api/insight/user/user_002/tag",
            json={"tag_name": "vip_status", "tag_value": "gold"}
        )

        # 查询
        response = await insight_client.get(
            "/api/insight/user/tags/by-value?tag_name=vip_status&tag_value=gold"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["tag_name"] == "vip_status"
        assert "user_ids" in data


class TestInsightProfile:
    """Insight 服务画像管理测试"""

    @pytest.mark.asyncio
    async def test_get_user_profile_not_found(self, insight_client: AsyncClient):
        """测试获取不存在的用户画像"""
        response = await insight_client.get("/api/insight/user/nonexistent_user/profile")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user_profile(self, insight_client: AsyncClient, generate_user_id: str):
        """测试更新用户画像"""
        response = await insight_client.put(
            f"/api/insight/user/{generate_user_id}/profile",
            json={
                "basic_info": {"name": "Test User", "email": "test@example.com"},
                "behavior_tags": ["active", "buyer"],
                "risk_level": "low"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["basic_info"]["name"] == "Test User"
        assert data["risk_level"] == "low"

    @pytest.mark.asyncio
    async def test_get_user_profile(self, insight_client: AsyncClient, generate_user_id: str):
        """测试获取用户画像"""
        # 先创建画像
        await insight_client.put(
            f"/api/insight/user/{generate_user_id}/profile",
            json={
                "basic_info": {"name": "Test"},
                "risk_level": "medium"
            }
        )

        # 获取画像
        response = await insight_client.get(f"/api/insight/user/{generate_user_id}/profile")

        assert response.status_code == 200
        data = response.json()

        assert data["basic_info"]["name"] == "Test"

    @pytest.mark.asyncio
    async def test_get_user_stat_not_found(self, insight_client: AsyncClient):
        """测试获取不存在的用户统计"""
        response = await insight_client.get("/api/insight/user/nonexistent_user/stat")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_users_by_risk(self, insight_client: AsyncClient):
        """测试按风险等级获取用户"""
        for risk_level in ["low", "medium", "high"]:
            response = await insight_client.get(f"/api/insight/users/by-risk/{risk_level}")

            assert response.status_code == 200
            data = response.json()

            assert data["risk_level"] == risk_level
            assert "user_ids" in data
            assert "user_count" in data

    @pytest.mark.asyncio
    async def test_get_users_by_invalid_risk(self, insight_client: AsyncClient):
        """测试无效风险等级"""
        response = await insight_client.get("/api/insight/users/by-risk/invalid")

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_user(self, insight_client: AsyncClient, generate_user_id: str):
        """测试删除用户"""
        # 先创建用户
        await insight_client.put(
            f"/api/insight/user/{generate_user_id}/profile",
            json={"risk_level": "low"}
        )

        # 删除用户
        response = await insight_client.delete(f"/api/insight/user/{generate_user_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["deleted"] is True

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user(self, insight_client: AsyncClient):
        """测试删除不存在的用户"""
        response = await insight_client.delete("/api/insight/user/nonexistent_user")

        assert response.status_code == 404


class TestInsightStatistics:
    """Insight 服务统计测试"""

    @pytest.mark.asyncio
    async def test_get_tag_statistics(self, insight_client: AsyncClient):
        """测试获取标签统计"""
        response = await insight_client.get("/api/insight/tags/statistics")

        assert response.status_code == 200
        data = response.json()

        assert "total_users" in data
        assert "tag_counts" in data
