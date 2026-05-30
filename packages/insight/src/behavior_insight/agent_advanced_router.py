"""
Agent Advanced Analysis API

Real implementations using:
- AgentOptimizationEngine for optimization suggestions
- AgentComplianceChecker for compliance reports
- AgentGraphAnalyzer for dependency graph analysis
- AgentRepository for database-backed stats, profiles, and tags
"""

from datetime import UTC, datetime
from typing import Any

from behavior_core.utils.logging import get_logger
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from behavior_insight.agent_graph import AgentGraphAnalyzer
from behavior_insight.compliance_checker import AgentComplianceChecker
from behavior_insight.optimization_engine import AgentOptimizationEngine
from behavior_insight.repositories.agent_repo import AgentRepository

logger = get_logger(__name__)

router = APIRouter(prefix="/api/agents/advanced", tags=["agent-advanced"])


# ============================================================
# Response Models
# ============================================================


class BehaviorPatternResponse(BaseModel):
    agent_id: str
    patterns: list[dict[str, Any]]
    detected_at: datetime


class BottleneckResponse(BaseModel):
    agent_id: str
    dependency_count: int
    anomaly_score: float
    total_cost_usd: float


class OptimizationResponse(BaseModel):
    agent_id: str
    total_suggestions: int
    priority_summary: dict[str, int]
    suggestions: list[dict[str, Any]]


class ComplianceResponse(BaseModel):
    agent_id: str
    overall_status: str
    total_rules: int
    passed: int
    warnings: int
    violations: int
    results: list[dict[str, Any]]


# ============================================================
# Dependency Injection
# ============================================================


def get_agent_repo(request: Request) -> AgentRepository:
    """Get AgentRepository dependency from request state."""
    if hasattr(request.state, "db_session"):
        return AgentRepository(request.state.db_session)
    raise HTTPException(status_code=500, detail="Database session not available")


# ============================================================
# Pattern Detection Helpers
# ============================================================


def _detect_patterns_from_stats(
    agent_id: str, stats: dict[str, Any], tags: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Detect behavior patterns from agent statistics and tags."""
    patterns: list[dict[str, Any]] = []

    error_rate = stats.get("error_rate", 0)
    if error_rate > 0.15:
        patterns.append(
            {
                "name": "high_error_rate",
                "confidence": min(1.0, error_rate / 0.5),
                "description": f"Error rate {error_rate:.1%} exceeds normal threshold",
                "category": "reliability",
            }
        )

    retry_tag = tags.get("retry_loop_detected", {})
    if retry_tag.get("value") == "true":
        patterns.append(
            {
                "name": "error_recovery_loop",
                "confidence": retry_tag.get("confidence", 0.8),
                "description": "Agent is stuck in an error-recovery loop",
                "category": "behavior",
            }
        )

    total_tool_calls = stats.get("total_tool_calls", 0)
    total_events = stats.get("total_events", 1)
    if total_events > 0 and total_tool_calls / total_events > 0.7:
        patterns.append(
            {
                "name": "sequential_tool_use",
                "confidence": round(total_tool_calls / total_events, 2),
                "description": "Agent predominantly uses tool calls in sequence",
                "category": "behavior",
            }
        )

    cost_1d = stats.get("cost_1d", 0)
    cost_7d = stats.get("cost_7d", 0)
    if cost_7d > 0 and cost_1d > cost_7d / 3:
        patterns.append(
            {
                "name": "cost_acceleration",
                "confidence": min(1.0, cost_1d / (cost_7d / 7) / 2),
                "description": "Daily cost is accelerating relative to weekly average",
                "category": "cost",
            }
        )

    p95_latency = stats.get("p95_latency_ms", 0)
    avg_latency = stats.get("avg_latency_ms", 0)
    if avg_latency > 0 and p95_latency > avg_latency * 5:
        patterns.append(
            {
                "name": "latency_spike_pattern",
                "confidence": min(1.0, p95_latency / (avg_latency * 10)),
                "description": (
                    "P95 latency is significantly higher than average, indicating spike patterns"
                ),
                "category": "performance",
            }
        )

    timeout_rate = stats.get("timeout_rate", 0)
    if timeout_rate > 0.05:
        patterns.append(
            {
                "name": "frequent_timeouts",
                "confidence": min(1.0, timeout_rate / 0.2),
                "description": f"Timeout rate {timeout_rate:.1%} indicates resource contention",
                "category": "performance",
            }
        )

    capability_drift = tags.get("capability_drifted", {})
    if capability_drift.get("value") == "true":
        patterns.append(
            {
                "name": "capability_drift",
                "confidence": capability_drift.get("confidence", 0.7),
                "description": "Agent behavior has drifted from its declared capabilities",
                "category": "safety",
            }
        )

    return patterns


def _compute_anomaly_score(stats: dict[str, Any], tags: dict[str, dict[str, Any]]) -> float:
    """Compute a weighted anomaly score from agent stats and tags."""
    score = 0.0

    error_rate = stats.get("error_rate", 0)
    score += min(0.25, error_rate * 1.5)

    timeout_rate = stats.get("timeout_rate", 0)
    score += min(0.15, timeout_rate * 2.0)

    risk_score = stats.get("risk_score", 0) if "risk_score" in stats else 0
    score += risk_score * 0.2

    p95 = stats.get("p95_latency_ms", 0)
    if p95 > 10000:
        score += min(0.15, (p95 - 10000) / 50000)

    cost_1d = stats.get("cost_1d", 0)
    if cost_1d > 50:
        score += min(0.1, (cost_1d - 50) / 200)

    if tags.get("unauthorized_tool_use", {}).get("value") == "true":
        score += 0.1
    if tags.get("capability_drifted", {}).get("value") == "true":
        score += 0.05

    return round(min(1.0, score), 3)


def _score_to_level(score: float) -> str:
    """Convert numeric anomaly score to severity level."""
    if score >= 0.8:
        return "critical"
    elif score >= 0.6:
        return "high"
    elif score >= 0.4:
        return "medium"
    elif score >= 0.2:
        return "low"
    return "normal"


# ============================================================
# Advanced Analysis Endpoints
# ============================================================


@router.get("/{agent_id}/patterns")
async def get_agent_patterns(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repo),
) -> dict[str, Any]:
    """Get detected behavior patterns for an agent.

    Patterns are derived from the agent's current statistics and tags
    rather than from live event stream processing.
    """
    try:
        stats = await repo.get_agent_stats(agent_id)
        tags = await repo.get_agent_tags(agent_id)

        if stats is None:
            return {
                "agent_id": agent_id,
                "patterns": [],
                "detected_at": datetime.now(UTC).isoformat(),
            }

        patterns = _detect_patterns_from_stats(agent_id, stats, tags)

        return {
            "agent_id": agent_id,
            "patterns": patterns,
            "detected_at": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error("Failed to detect patterns", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to detect patterns")


@router.get("/{agent_id}/baseline")
async def get_agent_baseline(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repo),
) -> dict[str, Any]:
    """Get agent behavior baseline derived from stored statistics.

    The baseline is computed from the agent's aggregated stats in the
    database rather than from the stream processor's in-memory baseline.
    """
    try:
        stats = await repo.get_agent_stats(agent_id)
        profile = await repo.get_agent_profile(agent_id)

        if stats is None:
            return {
                "agent_id": agent_id,
                "baseline": None,
                "message": "No statistics available for this agent",
            }

        total_events = stats.get("total_events", 0)
        total_tokens = stats.get("total_tokens", 0)
        total_cost = stats.get("total_cost_usd", 0)
        avg_latency = stats.get("avg_latency_ms", 0)

        # Derive events-per-minute from the 1d window (1440 minutes)
        events_1d = stats.get("events_1d", 0)
        avg_events_per_minute = round(events_1d / 1440, 2) if events_1d > 0 else 0

        # Derive tokens per event
        avg_tokens_per_event = round(total_tokens / total_events, 0) if total_events > 0 else 0

        # Derive cost per hour from 1d cost
        cost_1d = stats.get("cost_1d", 0)
        avg_cost_per_hour = round(cost_1d / 24, 4) if cost_1d > 0 else 0.0

        # Typical tools and event types from profile capabilities
        capabilities = []
        supported_tools = []
        if profile:
            capabilities = profile.get("capabilities", [])
            supported_tools = profile.get("supported_tools", [])

        return {
            "agent_id": agent_id,
            "baseline": {
                "avg_events_per_minute": avg_events_per_minute,
                "avg_latency_ms": avg_latency,
                "avg_tokens_per_event": avg_tokens_per_event,
                "avg_cost_per_hour": avg_cost_per_hour,
                "typical_tools": supported_tools,
                "typical_event_types": capabilities,
                "error_rate_baseline": stats.get("error_rate", 0),
                "success_rate": stats.get("success_rate", 0),
                "p95_latency_ms": stats.get("p95_latency_ms", 0),
                "timeout_rate": stats.get("timeout_rate", 0),
                "total_events": total_events,
                "total_tokens": total_tokens,
                "total_cost_usd": total_cost,
            },
        }
    except Exception as e:
        logger.error("Failed to get baseline", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get baseline")


@router.get("/{agent_id}/optimization")
async def get_optimization_suggestions(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repo),
) -> dict[str, Any]:
    """Get optimization suggestions for an agent.

    Uses the AgentOptimizationEngine to analyze the agent's stats and
    profile, then generates a prioritized report of suggestions.
    """
    try:
        stats = await repo.get_agent_stats(agent_id)
        profile = await repo.get_agent_profile(agent_id)

        if not stats:
            return {
                "agent_id": agent_id,
                "total_suggestions": 0,
                "priority_summary": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "suggestions": [],
            }

        # Build the stats dict that the optimization engine expects
        engine_stats: dict[str, Any] = {
            "agent_id": agent_id,
            "total_cost_usd": stats.get("total_cost_usd", 0),
            "total_tasks": stats.get("total_tasks", 0),
            "total_tokens": stats.get("total_tokens", 0),
            "total_cached_tokens": stats.get("total_cached_tokens", 0),
            "error_rate": stats.get("error_rate", 0),
            "p95_latency_ms": stats.get("p95_latency_ms", 0),
            "timeout_rate": stats.get("timeout_rate", 0),
            "retry_rate": stats.get("retry_rate", 0),
            "completed_tasks": stats.get("completed_tasks", 0),
            "risk_score": profile.get("risk_score", 0) if profile else 0,
        }

        engine = AgentOptimizationEngine()
        suggestions = engine.analyze(engine_stats, profile)
        report = engine.generate_report(agent_id, suggestions)

        # Flatten suggestions for the response
        flat_suggestions = []
        for category_suggestions in report.get("by_category", {}).values():
            flat_suggestions.extend(category_suggestions)

        return {
            "agent_id": agent_id,
            "generated_at": report.get("generated_at"),
            "total_suggestions": report.get("total_suggestions", 0),
            "priority_summary": report.get("priority_summary", {}),
            "by_category": report.get("by_category", {}),
            "suggestions": flat_suggestions,
        }
    except Exception as e:
        logger.error("Failed to generate optimization suggestions", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate optimization suggestions")


@router.get("/{agent_id}/compliance")
async def get_compliance_report(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repo),
) -> dict[str, Any]:
    """Get compliance report for an agent.

    Uses the AgentComplianceChecker to evaluate the agent against all
    configured compliance rules.
    """
    try:
        stats = await repo.get_agent_stats(agent_id)
        profile = await repo.get_agent_profile(agent_id)
        tags = await repo.get_agent_tags(agent_id)

        if not stats:
            stats = {}

        checker = AgentComplianceChecker()
        report = checker.check(
            agent_id=agent_id,
            agent_stats=stats,
            agent_profile=profile,
            agent_tags=tags,
        )

        # Convert ComplianceResult objects to dicts
        results = []
        for r in report.results:
            results.append(
                {
                    "rule_id": r.rule_id,
                    "name": r.rule_name,
                    "status": r.status.value,
                    "message": r.message,
                    "details": r.details,
                    "checked_at": r.checked_at.isoformat(),
                }
            )

        return {
            "agent_id": report.agent_id,
            "checked_at": report.checked_at.isoformat(),
            "overall_status": report.overall_status.value,
            "total_rules": report.total_rules,
            "passed": report.passed,
            "warnings": report.warnings,
            "violations": report.violations,
            "results": results,
        }
    except Exception as e:
        logger.error("Failed to generate compliance report", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate compliance report")


@router.get("/graph")
async def get_agent_graph(
    repo: AgentRepository = Depends(get_agent_repo),
) -> dict[str, Any]:
    """Get agent dependency graph.

    Builds the graph from all agents in the database. Inter-agent
    relationships are inferred from delegation tags and shared tools.
    """
    try:
        # Fetch all agents
        agents, _ = await repo.list_agents(page=1, page_size=1000)

        analyzer = AgentGraphAnalyzer()

        # Add all agents as nodes
        for agent in agents:
            agent_id = agent["agent_id"]
            analyzer.add_agent(
                agent_id=agent_id,
                agent_type=agent.get("agent_type", "unknown"),
                model_name=agent.get("model_name"),
            )

            # Get stats for anomaly score
            stats = await repo.get_agent_stats(agent_id)
            tags = await repo.get_agent_tags(agent_id)

            anomaly_score = 0.0
            total_cost = 0.0
            total_events = 0
            if stats:
                anomaly_score = _compute_anomaly_score(stats, tags)
                total_cost = stats.get("total_cost_usd", 0)
                total_events = stats.get("total_events", 0)

            analyzer.update_agent_stats(
                agent_id=agent_id,
                events=total_events,
                cost=total_cost,
                anomaly_score=anomaly_score,
            )

            # Infer edges from tags (delegation, dependency)
            if tags.get("delegates_to"):
                target = tags["delegates_to"].get("value")
                if target:
                    analyzer.add_interaction(
                        source_id=agent_id,
                        target_id=target,
                        relationship="delegates_to",
                    )

            if tags.get("depends_on"):
                target = tags["depends_on"].get("value")
                if target:
                    analyzer.add_interaction(
                        source_id=agent_id,
                        target_id=target,
                        relationship="depends_on",
                    )

        graph = analyzer.get_graph()
        bottlenecks = analyzer.get_bottlenecks()
        communities = analyzer.get_communities()

        # Serialize nodes
        nodes = [
            {
                "agent_id": n.agent_id,
                "type": n.agent_type,
                "model_name": n.model_name,
                "status": n.status,
                "total_events": n.total_events,
                "total_cost_usd": round(n.total_cost_usd, 2),
                "anomaly_score": round(n.anomaly_score, 3),
            }
            for n in graph.nodes
        ]

        # Serialize edges
        edges = [
            {
                "source": e.source_agent_id,
                "target": e.target_agent_id,
                "relationship": e.relationship,
                "count": e.call_count,
                "avg_latency_ms": round(e.avg_latency_ms, 1),
            }
            for e in graph.edges
        ]

        # Serialize communities (sets -> lists)
        community_lists = [sorted(c) for c in communities]

        return {
            "nodes": nodes,
            "edges": edges,
            "bottlenecks": bottlenecks,
            "communities": community_lists,
            "critical_path": analyzer.get_critical_path(),
            "cycles": analyzer.detect_cycles(),
        }
    except Exception as e:
        logger.error("Failed to build agent graph", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to build agent graph")


@router.get("/anomaly-scores")
async def get_all_anomaly_scores(
    repo: AgentRepository = Depends(get_agent_repo),
) -> dict[str, Any]:
    """Get anomaly scores for all agents.

    Computes anomaly scores from each agent's stored statistics and tags
    rather than from the stream processor's live scorer.
    """
    try:
        agents, _ = await repo.list_agents(page=1, page_size=1000)

        results = []
        for agent in agents:
            agent_id = agent["agent_id"]
            stats = await repo.get_agent_stats(agent_id)
            tags = await repo.get_agent_tags(agent_id)

            if stats is None:
                continue

            score = _compute_anomaly_score(stats, tags)

            # Determine trend from time-windowed event counts
            events_1d = stats.get("events_1d", 0)
            events_7d = stats.get("events_7d", 0)
            avg_daily_7d = events_7d / 7 if events_7d > 0 else 0

            if avg_daily_7d > 0 and events_1d > avg_daily_7d * 1.5:
                trend = "increasing"
            elif avg_daily_7d > 0 and events_1d < avg_daily_7d * 0.5:
                trend = "decreasing"
            else:
                trend = "stable"

            results.append(
                {
                    "agent_id": agent_id,
                    "score": score,
                    "level": _score_to_level(score),
                    "trend": trend,
                    "error_rate": stats.get("error_rate", 0),
                    "timeout_rate": stats.get("timeout_rate", 0),
                }
            )

        # Sort by score descending (most anomalous first)
        results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "agents": results,
            "total": len(results),
            "updated_at": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error("Failed to get anomaly scores", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get anomaly scores")


@router.get("/trends/{agent_id}")
async def get_agent_trends(
    agent_id: str,
    period: str = Query("7d", description="Time period: 1d, 7d, 30d"),
    repo: AgentRepository = Depends(get_agent_repo),
) -> dict[str, Any]:
    """Get agent metric trends over time.

    Uses time-windowed statistics from the database (events_1d, events_7d,
    cost_1d, cost_7d, etc.) to compute current vs previous period comparisons.
    """
    try:
        stats = await repo.get_agent_stats(agent_id)

        if stats is None:
            return {
                "agent_id": agent_id,
                "period": period,
                "trends": {},
                "message": "No statistics available for this agent",
            }

        # Parse period
        period_days = 7
        if period.endswith("d"):
            try:
                period_days = int(period[:-1])
            except ValueError:
                period_days = 7

        # Build trends from available time-window data
        # Current period = the window matching the requested period
        # Previous period = the next larger window minus current
        trends: dict[str, dict[str, Any]] = {}

        def _prev_from_larger_window(current: float, larger_key: str, divisor: float) -> float:
            """Estimate previous period from a larger time window."""
            larger = stats.get(larger_key, 0)
            if larger > current:
                return (larger - current) / divisor
            return current

        if period_days <= 1:
            current_events = stats.get("events_1d", 0)
            current_tokens = stats.get("tokens_1d", 0)
            current_cost = stats.get("cost_1d", 0.0)
            prev_events = _prev_from_larger_window(current_events, "events_7d", 6)
            prev_tokens = _prev_from_larger_window(current_tokens, "tokens_7d", 6)
            prev_cost = _prev_from_larger_window(current_cost, "cost_7d", 6)
        elif period_days <= 7:
            current_events = stats.get("events_7d", 0)
            current_tokens = stats.get("tokens_7d", 0)
            current_cost = stats.get("cost_7d", 0.0)
            prev_events = _prev_from_larger_window(current_events, "events_30d", 3)
            prev_tokens = _prev_from_larger_window(current_tokens, "tokens_30d", 3)
            prev_cost = _prev_from_larger_window(current_cost, "cost_30d", 3)
        else:
            current_events = stats.get("events_30d", 0)
            current_tokens = stats.get("tokens_30d", 0)
            current_cost = stats.get("cost_30d", 0.0)
            prev_events = current_events
            prev_tokens = current_tokens
            prev_cost = current_cost

        def _change_pct(current: float, previous: float) -> float:
            if previous == 0:
                return 0.0
            return round((current - previous) / previous * 100, 1)

        trends["events"] = {
            "current": int(current_events),
            "previous": round(prev_events),
            "change_pct": _change_pct(current_events, prev_events),
        }
        trends["tokens"] = {
            "current": int(current_tokens),
            "previous": round(prev_tokens),
            "change_pct": _change_pct(current_tokens, prev_tokens),
        }
        trends["cost"] = {
            "current": round(current_cost, 2),
            "previous": round(prev_cost, 2),
            "change_pct": _change_pct(current_cost, prev_cost),
        }
        trends["success_rate"] = {
            "current": stats.get("success_rate", 0),
            "previous": stats.get("success_rate", 0),  # No historical comparison available
            "change_pct": 0.0,
        }
        trends["avg_latency"] = {
            "current": stats.get("avg_latency_ms", 0),
            "previous": stats.get("avg_latency_ms", 0),  # No historical comparison available
            "change_pct": 0.0,
        }
        trends["p95_latency"] = {
            "current": stats.get("p95_latency_ms", 0),
            "previous": stats.get("p95_latency_ms", 0),
            "change_pct": 0.0,
        }
        trends["error_rate"] = {
            "current": stats.get("error_rate", 0),
            "previous": stats.get("error_rate", 0),
            "change_pct": 0.0,
        }

        return {
            "agent_id": agent_id,
            "period": period,
            "trends": trends,
        }
    except Exception as e:
        logger.error("Failed to get agent trends", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get agent trends")
