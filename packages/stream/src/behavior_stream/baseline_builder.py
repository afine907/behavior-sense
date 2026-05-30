"""
AI Agent行为基线构建器
"""
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentBaseline:
    """Agent行为基线"""
    agent_id: str
    avg_events_per_minute: float = 0.0
    avg_latency_ms: float = 0.0
    avg_tokens_per_event: float = 0.0
    avg_cost_per_hour: float = 0.0
    typical_tools: set = field(default_factory=set)
    typical_event_types: set = field(default_factory=set)
    error_rate_baseline: float = 0.0
    sample_count: int = 0
    last_updated: float = 0.0


class BaselineBuilder:
    """行为基线构建器"""

    def __init__(self, window_size: int = 1000, min_samples: int = 50):
        self.window_size = window_size
        self.min_samples = min_samples
        self._agent_events: dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self._baselines: dict[str, AgentBaseline] = {}

    def add_event(self, agent_id: str, event: dict[str, Any]) -> None:
        """添加事件到基线构建窗口"""
        self._agent_events[agent_id].append({
            "timestamp": time.time(),
            "event_type": event.get("event_type"),
            "tool_name": event.get("tool_name"),
            "latency_ms": event.get("latency_ms", 0),
            "tokens": event.get("token_usage", {}).get("total_tokens", 0) if event.get("token_usage") else 0,
            "cost_usd": event.get("cost_usd", 0),
            "success": event.get("success", True),
        })

        # Auto-rebuild baseline if enough samples
        events = self._agent_events[agent_id]
        if len(events) >= self.min_samples and len(events) % 100 == 0:
            self.build_baseline(agent_id)

    def build_baseline(self, agent_id: str) -> AgentBaseline:
        """构建Agent行为基线"""
        events = list(self._agent_events.get(agent_id, []))

        if not events:
            return AgentBaseline(agent_id=agent_id)

        # Calculate metrics
        total = len(events)
        latencies = [e["latency_ms"] for e in events if e["latency_ms"] > 0]
        tokens = [e["tokens"] for e in events if e["tokens"] > 0]
        costs = [e["cost_usd"] for e in events if e["cost_usd"] > 0]
        errors = sum(1 for e in events if not e["success"])

        # Time-based rate
        if len(events) >= 2:
            time_span = events[-1]["timestamp"] - events[0]["timestamp"]
            events_per_minute = (total / max(time_span, 1)) * 60
        else:
            events_per_minute = 0

        # Collect typical tools and event types
        tool_counts: dict[str, int] = defaultdict(int)
        type_counts: dict[str, int] = defaultdict(int)
        for e in events:
            if e["tool_name"]:
                tool_counts[e["tool_name"]] += 1
            if e["event_type"]:
                type_counts[e["event_type"]] += 1

        # Keep tools/types used >10% of the time
        typical_tools = {t for t, c in tool_counts.items() if c / total > 0.1}
        typical_types = {t for t, c in type_counts.items() if c / total > 0.1}

        baseline = AgentBaseline(
            agent_id=agent_id,
            avg_events_per_minute=round(events_per_minute, 2),
            avg_latency_ms=round(sum(latencies) / max(len(latencies), 1), 1),
            avg_tokens_per_event=round(sum(tokens) / max(len(tokens), 1), 0),
            avg_cost_per_hour=round(sum(costs) / max(len(costs), 1) * events_per_minute * 60, 4),
            typical_tools=typical_tools,
            typical_event_types=typical_types,
            error_rate_baseline=round(errors / total, 4),
            sample_count=total,
            last_updated=time.time(),
        )

        self._baselines[agent_id] = baseline
        return baseline

    def get_baseline(self, agent_id: str) -> AgentBaseline | None:
        """获取Agent基线"""
        return self._baselines.get(agent_id)

    def detect_deviation(self, agent_id: str, event: dict[str, Any]) -> list[dict]:
        """检测事件是否偏离基线"""
        baseline = self._baselines.get(agent_id)
        if not baseline or baseline.sample_count < self.min_samples:
            return []

        deviations = []

        # Check latency deviation
        latency = event.get("latency_ms", 0)
        if latency > 0 and baseline.avg_latency_ms > 0:
            ratio = latency / baseline.avg_latency_ms
            if ratio > 3.0:
                deviations.append({
                    "type": "latency_deviation",
                    "current": latency,
                    "baseline": baseline.avg_latency_ms,
                    "ratio": round(ratio, 2),
                })

        # Check tool deviation
        tool = event.get("tool_name")
        if tool and tool not in baseline.typical_tools:
            deviations.append({
                "type": "tool_deviation",
                "current": tool,
                "typical": list(baseline.typical_tools),
            })

        # Check event type deviation
        event_type = event.get("event_type")
        if event_type and event_type not in baseline.typical_event_types:
            deviations.append({
                "type": "event_type_deviation",
                "current": event_type,
                "typical": list(baseline.typical_event_types),
            })

        return deviations

    def get_all_baselines(self) -> dict[str, AgentBaseline]:
        """获取所有基线"""
        return dict(self._baselines)
