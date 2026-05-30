"""
AI Agent异常评分系统
"""
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnomalyDimension:
    """单个异常维度"""
    name: str
    weight: float = 1.0
    score: float = 0.0  # 0.0-1.0
    details: dict = field(default_factory=dict)


class AgentAnomalyScorer:
    """Agent异常评分器 - 综合多个维度计算异常分数"""

    def __init__(self):
        # Per-agent scoring history
        self._agent_scores: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._agent_baselines: dict[str, dict] = {}

        # Dimension weights
        self.dimension_weights = {
            "loop_score": 0.25,
            "cost_score": 0.20,
            "error_score": 0.15,
            "latency_score": 0.15,
            "tool_abuse_score": 0.10,
            "capability_drift_score": 0.10,
            "security_score": 0.05,
        }

    def score_event(self, event: dict[str, Any], alerts: list[dict]) -> dict[str, Any]:
        """对单个事件计算异常分数"""
        agent_id = event.get("agent_id", "unknown")
        dimensions = []

        # Loop score
        loop_alerts = [a for a in alerts if a.get("detector") == "loop"]
        loop_dim = AnomalyDimension(
            name="loop_score",
            weight=self.dimension_weights["loop_score"],
            score=min(1.0, len(loop_alerts) * 0.3),
            details={"loop_alerts": len(loop_alerts)},
        )
        dimensions.append(loop_dim)

        # Cost score
        cost_usd = event.get("cost_usd", 0)
        cost_dim = AnomalyDimension(
            name="cost_score",
            weight=self.dimension_weights["cost_score"],
            score=min(1.0, cost_usd / 5.0),  # $5 = score 1.0
            details={"cost_usd": cost_usd},
        )
        dimensions.append(cost_dim)

        # Error score
        is_error = event.get("success") is False
        error_dim = AnomalyDimension(
            name="error_score",
            weight=self.dimension_weights["error_score"],
            score=1.0 if is_error else 0.0,
            details={"is_error": is_error},
        )
        dimensions.append(error_dim)

        # Latency score
        latency_ms = event.get("latency_ms", 0)
        latency_score = min(1.0, latency_ms / 30000)  # 30s = score 1.0
        latency_dim = AnomalyDimension(
            name="latency_score",
            weight=self.dimension_weights["latency_score"],
            score=latency_score,
            details={"latency_ms": latency_ms},
        )
        dimensions.append(latency_dim)

        # Tool abuse score
        tool_abuse_alerts = [a for a in alerts if a.get("detector") == "tool_abuse"]
        tool_dim = AnomalyDimension(
            name="tool_abuse_score",
            weight=self.dimension_weights["tool_abuse_score"],
            score=min(1.0, len(tool_abuse_alerts) * 0.4),
            details={"tool_abuse_alerts": len(tool_abuse_alerts)},
        )
        dimensions.append(tool_dim)

        # Capability drift score
        drift_alerts = [a for a in alerts if a.get("detector") == "capability_drift"]
        drift_dim = AnomalyDimension(
            name="capability_drift_score",
            weight=self.dimension_weights["capability_drift_score"],
            score=min(1.0, len(drift_alerts) * 0.5),
            details={"drift_alerts": len(drift_alerts)},
        )
        dimensions.append(drift_dim)

        # Security score
        security_alerts = [a for a in alerts if a.get("detector") in ("prompt_injection", "data_exfiltration")]
        security_dim = AnomalyDimension(
            name="security_score",
            weight=self.dimension_weights["security_score"],
            score=min(1.0, len(security_alerts) * 0.8),
            details={"security_alerts": len(security_alerts)},
        )
        dimensions.append(security_dim)

        # Calculate weighted total
        total_score = sum(d.score * d.weight for d in dimensions)
        total_score = min(1.0, total_score)

        # Store in history
        self._agent_scores[agent_id].append({
            "score": total_score,
            "timestamp": time.time(),
            "dimensions": {d.name: d.score for d in dimensions},
        })

        return {
            "agent_id": agent_id,
            "anomaly_score": round(total_score, 3),
            "anomaly_level": self._score_to_level(total_score),
            "dimensions": [
                {
                    "name": d.name,
                    "score": round(d.score, 3),
                    "weight": d.weight,
                    "weighted_score": round(d.score * d.weight, 3),
                    "details": d.details,
                }
                for d in dimensions
            ],
            "timestamp": time.time(),
        }

    def get_agent_trend(self, agent_id: str, window_seconds: int = 300) -> dict[str, Any]:
        """获取Agent异常分数趋势"""
        history = self._agent_scores.get(agent_id, deque())
        cutoff = time.time() - window_seconds

        recent = [h for h in history if h["timestamp"] >= cutoff]

        if not recent:
            return {
                "agent_id": agent_id,
                "trend": "stable",
                "avg_score": 0.0,
                "max_score": 0.0,
                "sample_count": 0,
            }

        scores = [h["score"] for h in recent]
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)

        # Determine trend
        if len(scores) >= 3:
            first_half = scores[:len(scores)//2]
            second_half = scores[len(scores)//2:]
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)

            if second_avg > first_avg * 1.2:
                trend = "increasing"
            elif second_avg < first_avg * 0.8:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "agent_id": agent_id,
            "trend": trend,
            "avg_score": round(avg_score, 3),
            "max_score": round(max_score, 3),
            "current_score": round(scores[-1], 3),
            "sample_count": len(scores),
        }

    def get_all_agents_scores(self) -> list[dict]:
        """获取所有Agent的当前异常分数"""
        results = []
        for agent_id, history in self._agent_scores.items():
            if history:
                latest = history[-1]
                results.append({
                    "agent_id": agent_id,
                    "current_score": round(latest["score"], 3),
                    "anomaly_level": self._score_to_level(latest["score"]),
                    "trend": self.get_agent_trend(agent_id)["trend"],
                })

        results.sort(key=lambda x: x["current_score"], reverse=True)
        return results

    def _score_to_level(self, score: float) -> str:
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        elif score >= 0.2:
            return "low"
        return "normal"
