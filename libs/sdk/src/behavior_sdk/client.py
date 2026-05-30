"""
BehaviorSense SDK客户端
"""
from typing import Any

import httpx

from behavior_sdk.models import AgentEvent, AgentProfile


class BehaviorSenseClient:
    """BehaviorSense API客户端"""

    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        api_key: str | None = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    # ============================================================
    # Event Tracking
    # ============================================================

    async def track_event(self, event: AgentEvent) -> dict[str, Any]:
        """发送Agent事件"""
        client = await self._get_client()
        response = await client.post(
            "/api/agent-mock/generate",
            json=event.model_dump(),
        )
        response.raise_for_status()
        return response.json()

    async def track_events(self, events: list[AgentEvent]) -> dict[str, Any]:
        """批量发送Agent事件"""
        client = await self._get_client()
        response = await client.post(
            "/api/agent-mock/generate",
            json={"events": [e.model_dump() for e in events]},
        )
        response.raise_for_status()
        return response.json()

    # ============================================================
    # Agent Management
    # ============================================================

    async def get_agent(self, agent_id: str) -> AgentProfile:
        """获取Agent信息"""
        client = await self._get_client()
        response = await client.get(f"/api/agents/{agent_id}")
        response.raise_for_status()
        return AgentProfile(**response.json())

    async def create_agent(self, agent: AgentProfile) -> AgentProfile:
        """创建Agent"""
        client = await self._get_client()
        response = await client.put(
            f"/api/agents/{agent.agent_id}",
            json=agent.model_dump(),
        )
        response.raise_for_status()
        return AgentProfile(**response.json())

    async def delete_agent(self, agent_id: str) -> bool:
        """删除Agent"""
        client = await self._get_client()
        response = await client.delete(f"/api/agents/{agent_id}")
        return response.status_code == 200

    async def list_agents(
        self,
        agent_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """列出Agent"""
        client = await self._get_client()
        params = {"page": page, "page_size": page_size}
        if agent_type:
            params["agent_type"] = agent_type
        if status:
            params["status"] = status
        response = await client.get("/api/agents", params=params)
        response.raise_for_status()
        return response.json()

    # ============================================================
    # Agent Tags
    # ============================================================

    async def get_agent_tags(self, agent_id: str) -> dict[str, Any]:
        """获取Agent标签"""
        client = await self._get_client()
        response = await client.get(f"/api/agents/{agent_id}/tags")
        response.raise_for_status()
        return response.json()

    async def set_agent_tag(
        self,
        agent_id: str,
        tag_name: str,
        tag_value: str,
        source: str = "SDK",
    ) -> bool:
        """设置Agent标签"""
        client = await self._get_client()
        response = await client.put(
            f"/api/agents/{agent_id}/tags",
            json={"tag_name": tag_name, "tag_value": tag_value, "source": source},
        )
        return response.status_code == 200

    # ============================================================
    # Agent Statistics
    # ============================================================

    async def get_agent_stats(self, agent_id: str) -> dict[str, Any]:
        """获取Agent统计"""
        client = await self._get_client()
        response = await client.get(f"/api/agents/{agent_id}/stats")
        response.raise_for_status()
        return response.json()

    async def get_agent_cost(self, agent_id: str) -> dict[str, Any]:
        """获取Agent成本"""
        client = await self._get_client()
        response = await client.get(f"/api/agents/{agent_id}/stats/cost")
        response.raise_for_status()
        return response.json()

    async def get_agent_performance(self, agent_id: str) -> dict[str, Any]:
        """获取Agent性能"""
        client = await self._get_client()
        response = await client.get(f"/api/agents/{agent_id}/stats/performance")
        response.raise_for_status()
        return response.json()

    async def get_agent_risk(self, agent_id: str) -> dict[str, Any]:
        """获取Agent风险评估"""
        client = await self._get_client()
        response = await client.get(f"/api/agents/{agent_id}/risk")
        response.raise_for_status()
        return response.json()

    async def get_agent_capabilities(self, agent_id: str) -> dict[str, Any]:
        """获取Agent能力"""
        client = await self._get_client()
        response = await client.get(f"/api/agents/{agent_id}/capabilities")
        response.raise_for_status()
        return response.json()

    # ============================================================
    # Traces
    # ============================================================

    async def list_traces(
        self,
        agent_id: str | None = None,
        has_error: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """列出Trace"""
        client = await self._get_client()
        params = {"page": page, "page_size": page_size}
        if agent_id:
            params["agent_id"] = agent_id
        if has_error is not None:
            params["has_error"] = has_error
        response = await client.get("/api/traces", params=params)
        response.raise_for_status()
        return response.json()

    async def get_trace(self, trace_id: str) -> dict[str, Any]:
        """获取Trace详情"""
        client = await self._get_client()
        response = await client.get(f"/api/traces/{trace_id}")
        response.raise_for_status()
        return response.json()

    async def get_trace_waterfall(self, trace_id: str) -> dict[str, Any]:
        """获取Trace瀑布图"""
        client = await self._get_client()
        response = await client.get(f"/api/traces/{trace_id}/waterfall")
        response.raise_for_status()
        return response.json()

    # ============================================================
    # Advanced Analytics
    # ============================================================

    async def get_agent_graph(self) -> dict[str, Any]:
        """获取Agent关系图"""
        client = await self._get_client()
        response = await client.get("/api/agents/advanced/graph")
        response.raise_for_status()
        return response.json()

    async def get_anomaly_scores(self) -> dict[str, Any]:
        """获取异常评分"""
        client = await self._get_client()
        response = await client.get("/api/agents/advanced/anomaly-scores")
        response.raise_for_status()
        return response.json()

    async def get_optimization_suggestions(self, agent_id: str) -> dict[str, Any]:
        """获取优化建议"""
        client = await self._get_client()
        response = await client.get(f"/api/agents/advanced/{agent_id}/optimization")
        response.raise_for_status()
        return response.json()

    async def get_compliance_report(self, agent_id: str) -> dict[str, Any]:
        """获取合规报告"""
        client = await self._get_client()
        response = await client.get(f"/api/agents/advanced/{agent_id}/compliance")
        response.raise_for_status()
        return response.json()

    # ============================================================
    # Scenarios
    # ============================================================

    async def start_scenario(self, scenario: str, params: dict | None = None) -> dict[str, Any]:
        """启动模拟场景"""
        client = await self._get_client()
        response = await client.post(
            "/api/agent-mock/scenario/start",
            json={"scenario": scenario, "params": params or {}},
        )
        response.raise_for_status()
        return response.json()

    # ============================================================
    # Global Stats
    # ============================================================

    async def get_overview(self) -> dict[str, Any]:
        """获取全局概览"""
        client = await self._get_client()
        response = await client.get("/api/agents/stats/overview")
        response.raise_for_status()
        return response.json()

    async def get_cost_summary(self) -> dict[str, Any]:
        """获取成本汇总"""
        client = await self._get_client()
        response = await client.get("/api/agents/stats/cost")
        response.raise_for_status()
        return response.json()
