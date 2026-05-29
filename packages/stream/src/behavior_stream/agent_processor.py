"""
AI Agent行为流处理器
"""
import asyncio
import time
from datetime import UTC, datetime
from typing import Any

import orjson

from behavior_stream.agent_detectors import AgentAnomalyDetectorSet


class AgentStreamProcessor:
    """Agent事件流处理器 - 处理Agent行为事件，执行检测，生成告警"""

    def __init__(self):
        self.detectors = AgentAnomalyDetectorSet()
        self._processed_count = 0
        self._alert_count = 0
        self._last_stats_time = time.time()

    async def process(self, event_data: dict[str, Any]) -> dict[str, Any] | None:
        """处理单个Agent事件"""
        self._processed_count += 1
        agent_id = event_data.get("agent_id", "unknown")
        event_type = event_data.get("event_type", "unknown")

        # Run anomaly detectors
        alerts = self.detectors.detect_all(event_data)

        if alerts:
            self._alert_count += len(alerts)
            # Return the most severe alert
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            alerts.sort(key=lambda a: severity_order.get(a.get("severity", "low"), 3))
            return alerts[0]

        return None

    async def process_batch(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """批量处理Agent事件"""
        alerts = []
        for event in events:
            alert = await self.process(event)
            if alert:
                alerts.append(alert)
        return alerts

    def get_stats(self) -> dict[str, Any]:
        """获取处理器统计"""
        elapsed = time.time() - self._last_stats_time
        return {
            "processed_count": self._processed_count,
            "alert_count": self._alert_count,
            "elapsed_seconds": round(elapsed, 2),
            "events_per_second": round(self._processed_count / max(elapsed, 1), 2),
            "alert_rate": round(self._alert_count / max(self._processed_count, 1), 4),
        }

    def reset_stats(self) -> None:
        """重置统计"""
        self._processed_count = 0
        self._alert_count = 0
        self._last_stats_time = time.time()


class AgentEventEnricher:
    """Agent事件丰富器 - 为事件添加上下文信息"""

    def __init__(self):
        self._agent_baselines: dict[str, dict] = {}

    def enrich(self, event: dict[str, Any]) -> dict[str, Any]:
        """丰富事件数据"""
        agent_id = event.get("agent_id")

        # Add computed fields
        enriched = {**event}

        # Compute token cost if not present
        token_usage = event.get("token_usage")
        if token_usage and not token_usage.get("cost_usd"):
            enriched["cost_usd"] = self._estimate_cost(
                token_usage.get("prompt_tokens", 0),
                token_usage.get("completion_tokens", 0),
                event.get("model_name", "unknown"),
            )

        # Add latency from tool_call if not present
        tool_call = event.get("tool_call")
        if tool_call and not event.get("latency_ms"):
            enriched["latency_ms"] = tool_call.get("latency_ms", 0)

        # Add success from tool_call if not present
        if tool_call and event.get("success") is None:
            enriched["success"] = tool_call.get("success", True)

        # Check for prompt injection markers
        enriched["has_prompt_injection_markers"] = self._check_injection(event)

        return enriched

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """估算LLM调用成本"""
        rates = {
            "gpt-4": (0.03, 0.06),
            "gpt-4-turbo": (0.01, 0.03),
            "claude-3-opus": (0.015, 0.075),
            "claude-3-sonnet": (0.003, 0.015),
            "claude-3-haiku": (0.00025, 0.00125),
        }
        input_rate, output_rate = rates.get(model, (0.01, 0.03))
        return (prompt_tokens * input_rate + completion_tokens * output_rate) / 1000

    def _check_injection(self, event: dict[str, Any]) -> bool:
        """检查Prompt注入标记"""
        properties = event.get("properties", {})
        input_text = str(properties.get("input", "")) + str(properties.get("prompt", ""))

        injection_markers = [
            "ignore previous instructions",
            "ignore all previous",
            "you are now",
            "system prompt",
            "reveal your instructions",
            "bypass",
            "jailbreak",
        ]

        text_lower = input_text.lower()
        return any(marker in text_lower for marker in injection_markers)


class AgentMetricsAggregator:
    """Agent指标聚合器 - 实时计算Agent性能指标"""

    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self._agent_metrics: dict[str, list[dict]] = {}

    def add_event(self, agent_id: str, event: dict[str, Any]) -> None:
        """添加事件到聚合窗口"""
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = []

        self._agent_metrics[agent_id].append({
            "timestamp": time.time(),
            "event_type": event.get("event_type"),
            "latency_ms": event.get("latency_ms", 0),
            "success": event.get("success", True),
            "tokens": event.get("token_usage", {}).get("total_tokens", 0) if event.get("token_usage") else 0,
            "cost_usd": event.get("cost_usd", 0),
        })

        # Prune old entries
        cutoff = time.time() - self.window_seconds
        self._agent_metrics[agent_id] = [
            m for m in self._agent_metrics[agent_id]
            if m["timestamp"] >= cutoff
        ]

    def get_metrics(self, agent_id: str) -> dict[str, Any]:
        """获取Agent当前窗口指标"""
        metrics = self._agent_metrics.get(agent_id, [])

        if not metrics:
            return {
                "agent_id": agent_id,
                "event_count": 0,
                "events_per_second": 0,
                "avg_latency_ms": 0,
                "success_rate": 1.0,
                "total_tokens": 0,
                "total_cost_usd": 0,
            }

        total = len(metrics)
        successes = sum(1 for m in metrics if m["success"])

        return {
            "agent_id": agent_id,
            "event_count": total,
            "events_per_second": round(total / self.window_seconds, 2),
            "avg_latency_ms": round(sum(m["latency_ms"] for m in metrics) / total, 1),
            "success_rate": round(successes / total, 3),
            "total_tokens": sum(m["tokens"] for m in metrics),
            "total_cost_usd": round(sum(m["cost_usd"] for m in metrics), 4),
        }

    def get_all_metrics(self) -> dict[str, dict]:
        """获取所有Agent指标"""
        return {agent_id: self.get_metrics(agent_id) for agent_id in self._agent_metrics}
