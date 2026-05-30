"""
AI Agent优化建议引擎
"""
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class OptimizationSuggestion(BaseModel):
    """优化建议"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    agent_id: str
    category: str  # cost, performance, safety, efficiency
    priority: str  # low, medium, high, critical
    title: str
    description: str
    current_value: Any = None
    suggested_value: Any = None
    expected_improvement: str = ""
    implementation_effort: str = "low"  # low, medium, high
    created_at: datetime = Field(default_factory=_utc_now)


class AgentOptimizationEngine:
    """Agent优化建议引擎"""

    def __init__(self):
        self._thresholds = {
            "cost_per_task_high": 5.0,
            "error_rate_high": 0.15,
            "latency_p95_high": 10000,  # ms
            "token_per_task_high": 50000,
            "retry_rate_high": 0.2,
            "tool_misuse_rate_high": 0.1,
        }

    def analyze(self, agent_stats: dict[str, Any],
                agent_profile: dict[str, Any] | None = None) -> list[OptimizationSuggestion]:
        """分析Agent并生成优化建议"""
        suggestions = []
        agent_id = agent_stats.get("agent_id", "unknown")

        # Cost optimization
        suggestions.extend(self._analyze_cost(agent_id, agent_stats))

        # Performance optimization
        suggestions.extend(self._analyze_performance(agent_id, agent_stats))

        # Safety optimization
        suggestions.extend(self._analyze_safety(agent_id, agent_stats, agent_profile))

        # Efficiency optimization
        suggestions.extend(self._analyze_efficiency(agent_id, agent_stats))

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        suggestions.sort(key=lambda s: priority_order.get(s.priority, 3))

        return suggestions

    def _analyze_cost(self, agent_id: str, stats: dict) -> list[OptimizationSuggestion]:
        """分析成本相关优化"""
        suggestions = []

        total_cost = stats.get("total_cost_usd", 0)
        total_tasks = stats.get("total_tasks", 1)
        cost_per_task = total_cost / max(total_tasks, 1)

        if cost_per_task > self._thresholds["cost_per_task_high"]:
            suggestions.append(OptimizationSuggestion(
                agent_id=agent_id,
                category="cost",
                priority="high",
                title="High Cost Per Task",
                description=f"Average cost per task is ${cost_per_task:.2f}, which exceeds the threshold of ${self._thresholds['cost_per_task_high']:.2f}",
                current_value=round(cost_per_task, 2),
                suggested_value=self._thresholds["cost_per_task_high"],
                expected_improvement="Reduce cost per task by optimizing prompt length and model selection",
                implementation_effort="medium",
            ))

        # Check token usage efficiency
        total_tokens = stats.get("total_tokens", 0)
        token_per_task = total_tokens / max(total_tasks, 1)

        if token_per_task > self._thresholds["token_per_task_high"]:
            suggestions.append(OptimizationSuggestion(
                agent_id=agent_id,
                category="cost",
                priority="medium",
                title="High Token Usage Per Task",
                description=f"Average {token_per_task:.0f} tokens per task. Consider using shorter prompts or a more efficient model.",
                current_value=int(token_per_task),
                suggested_value=self._thresholds["token_per_task_high"],
                expected_improvement="Reduce token consumption by 30-50%",
                implementation_effort="medium",
            ))

        # Check cache utilization
        cached_tokens = stats.get("total_cached_tokens", 0)
        if total_tokens > 0 and cached_tokens / total_tokens < 0.1:
            suggestions.append(OptimizationSuggestion(
                agent_id=agent_id,
                category="cost",
                priority="low",
                title="Low Prompt Cache Utilization",
                description="Only {:.1%} of tokens are cached. Improve prompt caching to reduce costs.".format(cached_tokens / total_tokens),
                current_value=f"{cached_tokens}/{total_tokens}",
                suggested_value=">20% cache hit rate",
                expected_improvement="Reduce input token costs by 20-40%",
                implementation_effort="low",
            ))

        return suggestions

    def _analyze_performance(self, agent_id: str, stats: dict) -> list[OptimizationSuggestion]:
        """分析性能相关优化"""
        suggestions = []

        error_rate = stats.get("error_rate", 0)
        if error_rate > self._thresholds["error_rate_high"]:
            suggestions.append(OptimizationSuggestion(
                agent_id=agent_id,
                category="performance",
                priority="high",
                title="High Error Rate",
                description=f"Error rate is {error_rate:.1%}, exceeding threshold of {self._thresholds['error_rate_high']:.1%}",
                current_value=f"{error_rate:.1%}",
                suggested_value=f"<{self._thresholds['error_rate_high']:.1%}",
                expected_improvement="Improve reliability and user experience",
                implementation_effort="high",
            ))

        p95_latency = stats.get("p95_latency_ms", 0)
        if p95_latency > self._thresholds["latency_p95_high"]:
            suggestions.append(OptimizationSuggestion(
                agent_id=agent_id,
                category="performance",
                priority="medium",
                title="High P95 Latency",
                description=f"P95 latency is {p95_latency:.0f}ms, exceeding threshold of {self._thresholds['latency_p95_high']}ms",
                current_value=f"{p95_latency:.0f}ms",
                suggested_value=f"<{self._thresholds['latency_p95_high']}ms",
                expected_improvement="Improve response time for better user experience",
                implementation_effort="medium",
            ))

        timeout_rate = stats.get("timeout_rate", 0)
        if timeout_rate > 0.05:
            suggestions.append(OptimizationSuggestion(
                agent_id=agent_id,
                category="performance",
                priority="high",
                title="Frequent Timeouts",
                description=f"Timeout rate is {timeout_rate:.1%}. Review task complexity and timeout settings.",
                current_value=f"{timeout_rate:.1%}",
                suggested_value="<5%",
                expected_improvement="Reduce timeout frequency and improve task completion",
                implementation_effort="medium",
            ))

        return suggestions

    def _analyze_safety(self, agent_id: str, stats: dict,
                       profile: dict | None) -> list[OptimizationSuggestion]:
        """分析安全相关优化"""
        suggestions = []

        risk_score = stats.get("risk_score", 0)
        if risk_score > 0.5:
            suggestions.append(OptimizationSuggestion(
                agent_id=agent_id,
                category="safety",
                priority="critical",
                title="High Risk Score",
                description=f"Agent risk score is {risk_score:.2f}. Review and restrict capabilities.",
                current_value=round(risk_score, 2),
                suggested_value="<0.3",
                expected_improvement="Reduce security and compliance risk",
                implementation_effort="high",
            ))

        if profile:
            safety_rating = profile.get("safety_rating", "standard")
            if safety_rating in ("restricted", "quarantined"):
                suggestions.append(OptimizationSuggestion(
                    agent_id=agent_id,
                    category="safety",
                    priority="high",
                    title="Restricted Safety Rating",
                    description=f"Agent has '{safety_rating}' safety rating. Review recent behavior and restore trust.",
                    current_value=safety_rating,
                    suggested_value="standard",
                    expected_improvement="Restore full agent capabilities",
                    implementation_effort="medium",
                ))

        return suggestions

    def _analyze_efficiency(self, agent_id: str, stats: dict) -> list[OptimizationSuggestion]:
        """分析效率相关优化"""
        suggestions = []

        # Check task completion rate
        total_tasks = stats.get("total_tasks", 0)
        completed_tasks = stats.get("completed_tasks", 0)

        if total_tasks > 0 and completed_tasks / total_tasks < 0.8:
            suggestions.append(OptimizationSuggestion(
                agent_id=agent_id,
                category="efficiency",
                priority="medium",
                title="Low Task Completion Rate",
                description=f"Only {completed_tasks}/{total_tasks} tasks completed successfully.",
                current_value=f"{completed_tasks/total_tasks:.1%}",
                suggested_value=">80%",
                expected_improvement="Improve task success rate and reduce wasted resources",
                implementation_effort="medium",
            ))

        # Check retry rate
        retry_rate = stats.get("retry_rate", 0)
        if retry_rate > self._thresholds["retry_rate_high"]:
            suggestions.append(OptimizationSuggestion(
                agent_id=agent_id,
                category="efficiency",
                priority="medium",
                title="High Retry Rate",
                description=f"Retry rate is {retry_rate:.1%}. Review error handling and retry logic.",
                current_value=f"{retry_rate:.1%}",
                suggested_value=f"<{self._thresholds['retry_rate_high']:.1%}",
                expected_improvement="Reduce wasted resources from retries",
                implementation_effort="low",
            ))

        return suggestions

    def generate_report(self, agent_id: str, suggestions: list[OptimizationSuggestion]) -> dict[str, Any]:
        """生成优化报告"""
        by_category = {}
        for s in suggestions:
            if s.category not in by_category:
                by_category[s.category] = []
            by_category[s.category].append(s.model_dump())

        return {
            "agent_id": agent_id,
            "generated_at": _utc_now().isoformat(),
            "total_suggestions": len(suggestions),
            "by_category": by_category,
            "priority_summary": {
                "critical": sum(1 for s in suggestions if s.priority == "critical"),
                "high": sum(1 for s in suggestions if s.priority == "high"),
                "medium": sum(1 for s in suggestions if s.priority == "medium"),
                "low": sum(1 for s in suggestions if s.priority == "low"),
            },
        }
