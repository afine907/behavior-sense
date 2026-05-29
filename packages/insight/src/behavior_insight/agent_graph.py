"""
AI Agent关系图谱和依赖分析
"""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class AgentNode(BaseModel):
    """图中的Agent节点"""
    agent_id: str
    agent_type: str = "unknown"
    model_name: str | None = None
    status: str = "active"
    total_events: int = 0
    total_cost_usd: float = 0.0
    anomaly_score: float = 0.0


class AgentEdge(BaseModel):
    """Agent之间的关系边"""
    source_agent_id: str
    target_agent_id: str
    relationship: str  # "delegates_to", "depends_on", "shares_resource", "communicates"
    weight: float = 1.0  # relationship strength
    call_count: int = 0
    last_interaction: datetime | None = None
    avg_latency_ms: float = 0.0


class AgentGraph(BaseModel):
    """Agent关系图"""
    nodes: list[AgentNode] = Field(default_factory=list)
    edges: list[AgentEdge] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class AgentGraphAnalyzer:
    """Agent图谱分析器"""

    def __init__(self):
        self._nodes: dict[str, AgentNode] = {}
        self._edges: dict[tuple[str, str], AgentEdge] = {}
        self._adjacency: dict[str, set[str]] = defaultdict(set)

    def add_agent(self, agent_id: str, agent_type: str = "unknown",
                  model_name: str | None = None) -> None:
        """添加Agent节点"""
        if agent_id not in self._nodes:
            self._nodes[agent_id] = AgentNode(
                agent_id=agent_id,
                agent_type=agent_type,
                model_name=model_name,
            )

    def add_interaction(self, source_id: str, target_id: str,
                       relationship: str = "delegates_to",
                       latency_ms: float = 0) -> None:
        """添加Agent交互边"""
        key = (source_id, target_id)

        if key in self._edges:
            edge = self._edges[key]
            edge.call_count += 1
            edge.last_interaction = _utc_now()
            # Running average for latency
            if latency_ms > 0:
                edge.avg_latency_ms = (edge.avg_latency_ms * 0.9) + (latency_ms * 0.1)
        else:
            self._edges[key] = AgentEdge(
                source_agent_id=source_id,
                target_agent_id=target_id,
                relationship=relationship,
                call_count=1,
                last_interaction=_utc_now(),
                avg_latency_ms=latency_ms,
            )

        self._adjacency[source_id].add(target_id)

    def update_agent_stats(self, agent_id: str, events: int = 0,
                          cost: float = 0, anomaly_score: float = 0) -> None:
        """更新Agent统计"""
        if agent_id in self._nodes:
            node = self._nodes[agent_id]
            node.total_events += events
            node.total_cost_usd += cost
            node.anomaly_score = anomaly_score

    def get_graph(self) -> AgentGraph:
        """获取完整图"""
        return AgentGraph(
            nodes=list(self._nodes.values()),
            edges=list(self._edges.values()),
            updated_at=_utc_now(),
        )

    def get_dependencies(self, agent_id: str) -> dict[str, list[str]]:
        """获取Agent的依赖关系"""
        return {
            "depends_on": list(self._adjacency.get(agent_id, set())),
            "depended_by": [
                src for src, targets in self._adjacency.items()
                if agent_id in targets
            ],
        }

    def get_critical_path(self) -> list[str]:
        """获取关键路径（从入口到最深节点的最长路径）"""
        if not self._adjacency:
            return []

        # Find root nodes (no incoming edges)
        all_targets = set()
        for targets in self._adjacency.values():
            all_targets.update(targets)

        roots = [n for n in self._nodes if n not in all_targets]
        if not roots:
            roots = list(self._nodes.keys())[:1]

        # BFS to find longest path
        best_path = []
        for root in roots:
            path = self._dfs_longest(root, set())
            if len(path) > len(best_path):
                best_path = path

        return best_path

    def _dfs_longest(self, node: str, visited: set[str]) -> list[str]:
        """DFS找最长路径"""
        if node in visited:
            return [node]

        visited.add(node)
        best_sub = []

        for neighbor in self._adjacency.get(node, set()):
            sub = self._dfs_longest(neighbor, visited.copy())
            if len(sub) > len(best_sub):
                best_sub = sub

        return [node] + best_sub

    def detect_cycles(self) -> list[list[str]]:
        """检测循环依赖"""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: list[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._adjacency.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])

            path.pop()
            rec_stack.remove(node)

        for node in self._nodes:
            if node not in visited:
                dfs(node, [])

        return cycles

    def get_bottlenecks(self) -> list[dict[str, Any]]:
        """识别瓶颈Agent（被最多Agent依赖的节点）"""
        in_degree = defaultdict(int)
        for targets in self._adjacency.values():
            for t in targets:
                in_degree[t] += 1

        bottlenecks = []
        for agent_id, degree in sorted(in_degree.items(), key=lambda x: -x[1]):
            if degree >= 2:  # At least 2 dependencies
                node = self._nodes.get(agent_id)
                bottlenecks.append({
                    "agent_id": agent_id,
                    "dependency_count": degree,
                    "anomaly_score": node.anomaly_score if node else 0,
                    "total_cost_usd": node.total_cost_usd if node else 0,
                })

        return bottlenecks

    def get_communities(self) -> list[set[str]]:
        """检测Agent社区（紧密连接的子图）"""
        if not self._nodes:
            return []

        # Simple connected components
        visited = set()
        communities = []

        for node in self._nodes:
            if node not in visited:
                community = set()
                stack = [node]
                while stack:
                    current = stack.pop()
                    if current in visited:
                        continue
                    visited.add(current)
                    community.add(current)
                    # Add neighbors (both directions)
                    for neighbor in self._adjacency.get(current, set()):
                        if neighbor not in visited:
                            stack.append(neighbor)
                    for src, targets in self._adjacency.items():
                        if current in targets and src not in visited:
                            stack.append(src)
                communities.append(community)

        return communities

    def to_mermaid(self) -> str:
        """导出为Mermaid图格式"""
        lines = ["graph TD"]

        for node in self._nodes.values():
            style = ""
            if node.anomaly_score > 0.6:
                style = ":::critical"
            elif node.anomaly_score > 0.3:
                style = ":::warning"
            lines.append(f"    {node.agent_id}[\"{node.agent_id}\"]{style}")

        for edge in self._edges.values():
            label = f"|{edge.relationship}|"
            lines.append(f"    {edge.source_agent_id} -->{label} {edge.target_agent_id}")

        lines.extend([
            "",
            "    classDef critical fill:#ff6b6b,stroke:#333,stroke-width:2px",
            "    classDef warning fill:#ffd93d,stroke:#333,stroke-width:2px",
            "    classDef normal fill:#6bcb77,stroke:#333,stroke-width:2px",
        ])

        return "\n".join(lines)
