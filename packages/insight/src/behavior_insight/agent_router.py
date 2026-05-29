"""
AI Agent画像和洞察API
"""
from datetime import datetime

from behavior_core.utils.logging import get_logger
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from behavior_insight.repositories.agent_repo import AgentRepository

logger = get_logger(__name__)

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
    metrics: list[str] = Field(
        default_factory=lambda: ["success_rate", "avg_latency", "total_cost"]
    )


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
# Dependency Injection
# ============================================================


def get_agent_repo(request: Request) -> AgentRepository:
    """获取Agent仓库依赖"""
    # 使用 request.state（由 middleware 设置）
    if hasattr(request.state, "db_session"):
        return AgentRepository(request.state.db_session)
    # 回退到 app.state
    if hasattr(request.app.state, "async_session_factory"):
        # 如果没有 middleware session，使用 session factory
        raise HTTPException(
            status_code=500,
            detail="Database session not available",
        )
    raise HTTPException(status_code=500, detail="Database not configured")


# ============================================================
# Agent Profile Endpoints
# ============================================================


@router.get("", response_model=AgentListResponse)
async def list_agents(
    agent_type: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repo: AgentRepository = Depends(get_agent_repo),
):
    """List all agents with optional filtering"""
    try:
        agents, total = await repo.list_agents(
            agent_type=agent_type,
            status=status,
            page=page,
            page_size=page_size,
        )

        return AgentListResponse(
            agents=[AgentProfileResponse(**a) for a in agents],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error("Failed to list agents", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list agents")


@router.get("/{agent_id}", response_model=AgentProfileResponse)
async def get_agent_profile(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """Get agent profile by ID"""
    try:
        profile = await repo.get_agent_profile(agent_id)
        if not profile:
            raise HTTPException(
                status_code=404, detail=f"Agent {agent_id} not found"
            )
        return AgentProfileResponse(**profile)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get agent profile", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get agent profile")


@router.put("/{agent_id}")
async def update_agent_profile(
    agent_id: str,
    profile: dict,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """Update agent profile"""
    try:
        await repo.upsert_agent_profile(agent_id, profile)
        return {"status": "ok", "agent_id": agent_id}
    except Exception as e:
        logger.error("Failed to update agent profile", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update agent profile")


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """Delete agent and all associated data"""
    try:
        deleted = await repo.delete_agent(agent_id)
        if not deleted:
            raise HTTPException(
                status_code=404, detail=f"Agent {agent_id} not found"
            )
        return {"status": "ok", "agent_id": agent_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete agent", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete agent")


# ============================================================
# Agent Statistics Endpoints
# ============================================================


@router.get("/{agent_id}/stats", response_model=AgentStatResponse)
async def get_agent_stats(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """Get agent statistics"""
    try:
        stats = await repo.get_agent_stats(agent_id)
        if stats is None:
            # Return empty stats for non-existent agents
            return AgentStatResponse(agent_id=agent_id)
        return AgentStatResponse(**stats)
    except Exception as e:
        logger.error("Failed to get agent stats", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get agent stats")


@router.get("/{agent_id}/stats/cost")
async def get_agent_cost_breakdown(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """Get detailed cost breakdown for an agent"""
    try:
        stats = await repo.get_agent_stats(agent_id)
        if stats is None:
            stats = {}
        return {
            "agent_id": agent_id,
            "total_cost_usd": stats.get("total_cost_usd", 0.0),
            "cost_by_model": stats.get("cost_by_model", {}),
            "cost_by_tool": stats.get("cost_by_tool", {}),
            "cost_1d": stats.get("cost_1d", 0.0),
            "cost_7d": stats.get("cost_7d", 0.0),
            "cost_30d": stats.get("cost_30d", 0.0),
        }
    except Exception as e:
        logger.error("Failed to get agent cost breakdown", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get agent cost breakdown")


@router.get("/{agent_id}/stats/performance")
async def get_agent_performance(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """Get performance metrics for an agent"""
    try:
        stats = await repo.get_agent_stats(agent_id)
        if stats is None:
            stats = {}
        return {
            "agent_id": agent_id,
            "avg_latency_ms": stats.get("avg_latency_ms", 0.0),
            "p95_latency_ms": stats.get("p95_latency_ms", 0.0),
            "p99_latency_ms": stats.get("p99_latency_ms", 0.0),
            "success_rate": stats.get("success_rate", 0.0),
            "error_rate": stats.get("error_rate", 0.0),
            "timeout_rate": stats.get("timeout_rate", 0.0),
        }
    except Exception as e:
        logger.error("Failed to get agent performance", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get agent performance")


# ============================================================
# Agent Tags Endpoints
# ============================================================


@router.get("/{agent_id}/tags")
async def get_agent_tags(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """Get all tags for an agent"""
    try:
        tags = await repo.get_agent_tags(agent_id)
        return {
            "agent_id": agent_id,
            "tags": tags,
        }
    except Exception as e:
        logger.error("Failed to get agent tags", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get agent tags")


@router.put("/{agent_id}/tags")
async def update_agent_tag(
    agent_id: str,
    tag: AgentTagUpdate,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """Update a tag for an agent"""
    try:
        await repo.upsert_agent_tag(
            agent_id=agent_id,
            tag_name=tag.tag_name,
            tag_value=tag.tag_value,
            source=tag.source,
            confidence=tag.confidence,
        )
        return {"status": "ok", "agent_id": agent_id, "tag": tag.tag_name}
    except Exception as e:
        logger.error("Failed to update agent tag", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update agent tag")


@router.delete("/{agent_id}/tags/{tag_name}")
async def delete_agent_tag(
    agent_id: str,
    tag_name: str,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """Delete a tag from an agent"""
    try:
        deleted = await repo.delete_agent_tag(agent_id, tag_name)
        if not deleted:
            raise HTTPException(
                status_code=404, detail=f"Tag {tag_name} not found"
            )
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete agent tag", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete agent tag")


@router.get("/tags/by-value")
async def get_agents_by_tag(
    tag_name: str,
    tag_value: str | None = None,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """Find agents by tag name and optionally value"""
    try:
        result = await repo.get_agents_by_tag(tag_name, tag_value)
        return {
            "tag_name": tag_name,
            "agents": result,
            "count": len(result),
        }
    except Exception as e:
        logger.error("Failed to get agents by tag", tag_name=tag_name, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get agents by tag")


# ============================================================
# Agent Comparison & Analysis Endpoints
# ============================================================


@router.post("/compare", response_model=AgentComparisonResponse)
async def compare_agents(
    request: AgentComparisonRequest,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """Compare multiple agents across specified metrics"""
    try:
        result = await repo.get_agent_comparison(
            agent_ids=request.agent_ids,
            metrics=request.metrics,
        )
        return AgentComparisonResponse(**result)
    except Exception as e:
        logger.error("Failed to compare agents", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to compare agents")


@router.get("/{agent_id}/capabilities")
async def get_agent_capabilities(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """Get agent capability map"""
    try:
        profile = await repo.get_agent_profile(agent_id)
        if profile is None:
            raise HTTPException(
                status_code=404, detail=f"Agent {agent_id} not found"
            )
        return {
            "agent_id": agent_id,
            "capabilities": profile.get("capabilities", []),
            "supported_tools": profile.get("supported_tools", []),
            "capability_scores": profile.get("capability_scores", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get agent capabilities", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get agent capabilities")


@router.get("/{agent_id}/risk")
async def get_agent_risk_assessment(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """Get agent risk assessment"""
    try:
        profile = await repo.get_agent_profile(agent_id)
        stats = await repo.get_agent_stats(agent_id)
        tags = await repo.get_agent_tags(agent_id)

        if profile is None:
            raise HTTPException(
                status_code=404, detail=f"Agent {agent_id} not found"
            )

        if stats is None:
            stats = {}

        risk_factors = []
        risk_score = 0.0

        # Check error rate
        error_rate = stats.get("error_rate", 0)
        if error_rate > 0.3:
            risk_factors.append(
                {"factor": "high_error_rate", "value": error_rate, "weight": 0.3}
            )
            risk_score += 0.3

        # Check cost
        cost_1d = stats.get("cost_1d", 0)
        if cost_1d > 10:
            risk_factors.append(
                {"factor": "high_daily_cost", "value": cost_1d, "weight": 0.2}
            )
            risk_score += 0.2

        # Check safety tags
        if tags.get("pii_accessor", {}).get("value") == "true":
            risk_factors.append(
                {"factor": "pii_access", "value": True, "weight": 0.2}
            )
            risk_score += 0.2

        if tags.get("capability_drifted", {}).get("value") == "true":
            risk_factors.append(
                {"factor": "capability_drift", "value": True, "weight": 0.15}
            )
            risk_score += 0.15

        risk_score = min(risk_score, 1.0)

        risk_level = (
            "critical"
            if risk_score > 0.7
            else "high"
            if risk_score > 0.5
            else "medium"
            if risk_score > 0.3
            else "low"
        )

        return {
            "agent_id": agent_id,
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get agent risk assessment", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get agent risk assessment")


# ============================================================
# Global Statistics
# ============================================================


@router.get("/stats/overview")
async def get_agents_overview(
    repo: AgentRepository = Depends(get_agent_repo),
):
    """Get overview statistics for all agents"""
    try:
        return await repo.get_agents_overview()
    except Exception as e:
        logger.error("Failed to get agents overview", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get agents overview")


@router.get("/stats/cost")
async def get_cost_summary(
    repo: AgentRepository = Depends(get_agent_repo),
):
    """Get cost summary across all agents"""
    try:
        return await repo.get_cost_summary()
    except Exception as e:
        logger.error("Failed to get cost summary", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get cost summary")
