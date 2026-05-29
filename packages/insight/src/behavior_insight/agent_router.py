"""
AI Agent画像和洞察API
"""
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/agents", tags=["agent-insight"])


# ============================================================
# Request/Response Models
# ============================================================

class AgentProfileResponse(BaseModel):
    agent_id: str
    agent_name: str | None = None
    agent_type: str | None = None
    model_name: str | None = None
    framework: str | None = None
    owner: str | None = None
    status: str = "active"
    safety_rating: str = "standard"
    cost_tier: str = "standard"
    capabilities: list[str] = Field(default_factory=list)
    risk_score: float = 0.0
    create_time: datetime | None = None
    last_active: datetime | None = None


class AgentStatResponse(BaseModel):
    agent_id: str
    total_events: int = 0
    total_sessions: int = 0
    total_tasks: int = 0
    total_tool_calls: int = 0
    total_llm_calls: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    success_rate: float = 0.0
    error_rate: float = 0.0
    # Time windows
    events_1d: int = 0
    events_7d: int = 0
    tokens_1d: int = 0
    tokens_7d: int = 0
    cost_1d: float = 0.0
    cost_7d: float = 0.0


class AgentTagUpdate(BaseModel):
    tag_name: str
    tag_value: str
    source: str = "AUTO"
    confidence: float = 1.0


class AgentComparisonRequest(BaseModel):
    agent_ids: list[str]
    metrics: list[str] = Field(default_factory=lambda: ["success_rate", "avg_latency", "total_cost"])


class AgentComparisonResponse(BaseModel):
    agents: list[str]
    metrics: dict[str, dict[str, float]]
    rankings: dict[str, list[str]]
    insights: list[str]


class AgentListResponse(BaseModel):
    agents: list[AgentProfileResponse]
    total: int
    page: int
    page_size: int


# ============================================================
# Mock data store (in production, would use PostgreSQL + Redis)
# ============================================================
_agent_profiles: dict[str, dict] = {}
_agent_stats: dict[str, dict] = {}
_agent_tags: dict[str, dict[str, dict]] = {}


# ============================================================
# Agent Profile Endpoints
# ============================================================

@router.get("", response_model=AgentListResponse)
async def list_agents(
    agent_type: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all agents with optional filtering"""
    agents = list(_agent_profiles.values())

    if agent_type:
        agents = [a for a in agents if a.get("agent_type") == agent_type]
    if status:
        agents = [a for a in agents if a.get("status") == status]

    total = len(agents)
    start = (page - 1) * page_size
    end = start + page_size
    page_agents = agents[start:end]

    return AgentListResponse(
        agents=[AgentProfileResponse(**a) for a in page_agents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{agent_id}", response_model=AgentProfileResponse)
async def get_agent_profile(agent_id: str):
    """Get agent profile by ID"""
    if agent_id not in _agent_profiles:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AgentProfileResponse(**_agent_profiles[agent_id])


@router.put("/{agent_id}")
async def update_agent_profile(agent_id: str, profile: dict):
    """Update agent profile"""
    if agent_id in _agent_profiles:
        _agent_profiles[agent_id].update(profile)
    else:
        _agent_profiles[agent_id] = {"agent_id": agent_id, **profile}
    return {"status": "ok", "agent_id": agent_id}


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete agent and all associated data"""
    if agent_id in _agent_profiles:
        del _agent_profiles[agent_id]
    _agent_stats.pop(agent_id, None)
    _agent_tags.pop(agent_id, None)
    return {"status": "ok", "agent_id": agent_id}


# ============================================================
# Agent Statistics Endpoints
# ============================================================

@router.get("/{agent_id}/stats", response_model=AgentStatResponse)
async def get_agent_stats(agent_id: str):
    """Get agent statistics"""
    if agent_id not in _agent_stats:
        # Return empty stats
        return AgentStatResponse(agent_id=agent_id)
    return AgentStatResponse(**_agent_stats[agent_id])


@router.get("/{agent_id}/stats/cost")
async def get_agent_cost_breakdown(agent_id: str):
    """Get detailed cost breakdown for an agent"""
    stats = _agent_stats.get(agent_id, {})
    return {
        "agent_id": agent_id,
        "total_cost_usd": stats.get("total_cost_usd", 0.0),
        "cost_by_model": stats.get("cost_by_model", {}),
        "cost_by_tool": stats.get("cost_by_tool", {}),
        "cost_1d": stats.get("cost_1d", 0.0),
        "cost_7d": stats.get("cost_7d", 0.0),
        "cost_30d": stats.get("cost_30d", 0.0),
    }


@router.get("/{agent_id}/stats/performance")
async def get_agent_performance(agent_id: str):
    """Get performance metrics for an agent"""
    stats = _agent_stats.get(agent_id, {})
    return {
        "agent_id": agent_id,
        "avg_latency_ms": stats.get("avg_latency_ms", 0.0),
        "p95_latency_ms": stats.get("p95_latency_ms", 0.0),
        "p99_latency_ms": stats.get("p99_latency_ms", 0.0),
        "success_rate": stats.get("success_rate", 0.0),
        "error_rate": stats.get("error_rate", 0.0),
        "timeout_rate": stats.get("timeout_rate", 0.0),
    }


# ============================================================
# Agent Tags Endpoints
# ============================================================

@router.get("/{agent_id}/tags")
async def get_agent_tags(agent_id: str):
    """Get all tags for an agent"""
    return {
        "agent_id": agent_id,
        "tags": _agent_tags.get(agent_id, {}),
    }


@router.put("/{agent_id}/tags")
async def update_agent_tag(agent_id: str, tag: AgentTagUpdate):
    """Update a tag for an agent"""
    if agent_id not in _agent_tags:
        _agent_tags[agent_id] = {}

    _agent_tags[agent_id][tag.tag_name] = {
        "value": tag.tag_value,
        "source": tag.source,
        "confidence": tag.confidence,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    return {"status": "ok", "agent_id": agent_id, "tag": tag.tag_name}


@router.delete("/{agent_id}/tags/{tag_name}")
async def delete_agent_tag(agent_id: str, tag_name: str):
    """Delete a tag from an agent"""
    tags = _agent_tags.get(agent_id, {})
    if tag_name in tags:
        del tags[tag_name]
        return {"status": "ok"}
    raise HTTPException(status_code=404, detail=f"Tag {tag_name} not found")


@router.get("/tags/by-value")
async def get_agents_by_tag(tag_name: str, tag_value: str | None = None):
    """Find agents by tag name and optionally value"""
    result = []
    for agent_id, tags in _agent_tags.items():
        if tag_name in tags:
            if tag_value is None or tags[tag_name]["value"] == tag_value:
                result.append({"agent_id": agent_id, "tag": tags[tag_name]})
    return {"tag_name": tag_name, "agents": result, "count": len(result)}


# ============================================================
# Agent Comparison & Analysis Endpoints
# ============================================================

@router.post("/compare", response_model=AgentComparisonResponse)
async def compare_agents(request: AgentComparisonRequest):
    """Compare multiple agents across specified metrics"""
    metrics_data = {}
    rankings = {}

    for metric in request.metrics:
        metric_values = {}
        for agent_id in request.agent_ids:
            stats = _agent_stats.get(agent_id, {})
            metric_values[agent_id] = stats.get(metric, 0.0)

        metrics_data[metric] = metric_values

        # Sort by metric (lower is better for cost/latency, higher for success_rate)
        reverse = metric in ("success_rate",)
        sorted_agents = sorted(metric_values.keys(), key=lambda a: metric_values[a], reverse=reverse)
        rankings[metric] = sorted_agents

    # Generate insights
    insights = []
    if "success_rate" in rankings and len(request.agent_ids) > 1:
        best = rankings["success_rate"][0]
        worst = rankings["success_rate"][-1]
        insights.append(f"Best performing agent: {best}")
        if metrics_data["success_rate"][best] - metrics_data["success_rate"][worst] > 0.2:
            insights.append(f"Significant performance gap between {best} and {worst}")

    return AgentComparisonResponse(
        agents=request.agent_ids,
        metrics=metrics_data,
        rankings=rankings,
        insights=insights,
    )


@router.get("/{agent_id}/capabilities")
async def get_agent_capabilities(agent_id: str):
    """Get agent capability map"""
    profile = _agent_profiles.get(agent_id, {})
    return {
        "agent_id": agent_id,
        "capabilities": profile.get("capabilities", []),
        "supported_tools": profile.get("supported_tools", []),
        "capability_scores": profile.get("capability_scores", {}),
    }


@router.get("/{agent_id}/risk")
async def get_agent_risk_assessment(agent_id: str):
    """Get agent risk assessment"""
    profile = _agent_profiles.get(agent_id, {})
    stats = _agent_stats.get(agent_id, {})
    tags = _agent_tags.get(agent_id, {})

    risk_factors = []
    risk_score = 0.0

    # Check error rate
    error_rate = stats.get("error_rate", 0)
    if error_rate > 0.3:
        risk_factors.append({"factor": "high_error_rate", "value": error_rate, "weight": 0.3})
        risk_score += 0.3

    # Check cost
    cost_1d = stats.get("cost_1d", 0)
    if cost_1d > 10:
        risk_factors.append({"factor": "high_daily_cost", "value": cost_1d, "weight": 0.2})
        risk_score += 0.2

    # Check safety tags
    if tags.get("pii_accessor", {}).get("value") == "true":
        risk_factors.append({"factor": "pii_access", "value": True, "weight": 0.2})
        risk_score += 0.2

    if tags.get("capability_drifted", {}).get("value") == "true":
        risk_factors.append({"factor": "capability_drift", "value": True, "weight": 0.15})
        risk_score += 0.15

    risk_score = min(risk_score, 1.0)

    return {
        "agent_id": agent_id,
        "risk_score": round(risk_score, 2),
        "risk_level": "critical" if risk_score > 0.7 else "high" if risk_score > 0.5 else "medium" if risk_score > 0.3 else "low",
        "risk_factors": risk_factors,
    }


# ============================================================
# Global Statistics
# ============================================================

@router.get("/stats/overview")
async def get_agents_overview():
    """Get overview statistics for all agents"""
    total_agents = len(_agent_profiles)
    active_agents = sum(1 for a in _agent_profiles.values() if a.get("status") == "active")

    total_cost = sum(s.get("total_cost_usd", 0) for s in _agent_stats.values())
    total_events = sum(s.get("total_events", 0) for s in _agent_stats.values())
    total_tokens = sum(s.get("total_tokens", 0) for s in _agent_stats.values())

    avg_success_rate = 0.0
    if _agent_stats:
        rates = [s.get("success_rate", 0) for s in _agent_stats.values()]
        avg_success_rate = sum(rates) / len(rates) if rates else 0.0

    return {
        "total_agents": total_agents,
        "active_agents": active_agents,
        "total_cost_usd": round(total_cost, 2),
        "total_events": total_events,
        "total_tokens": total_tokens,
        "avg_success_rate": round(avg_success_rate, 3),
    }


@router.get("/stats/cost")
async def get_cost_summary():
    """Get cost summary across all agents"""
    by_agent = {}
    by_model = {}

    for agent_id, stats in _agent_stats.items():
        by_agent[agent_id] = stats.get("total_cost_usd", 0)
        for model, cost in stats.get("cost_by_model", {}).items():
            by_model[model] = by_model.get(model, 0) + cost

    return {
        "total_cost_usd": sum(by_agent.values()),
        "by_agent": by_agent,
        "by_model": by_model,
    }
