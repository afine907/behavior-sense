"""
AI Agent行为模拟API
"""
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/agent-mock", tags=["agent-mock"])


class GenerateAgentEventsRequest(BaseModel):
    """生成Agent事件请求"""
    agent_id: str | None = None
    agent_type: str = "llm_agent"
    model_name: str = "gpt-4"
    count: int = Field(default=10, ge=1, le=1000)
    event_types: list[str] | None = None
    include_tokens: bool = True
    include_tools: bool = True


class ScenarioRequest(BaseModel):
    """场景启动请求"""
    scenario: str  # normal, loop, cost_explosion, cascading_failure
    agent_count: int = Field(default=3, ge=1, le=20)
    duration_events: int = Field(default=100, ge=10, le=10000)
    params: dict[str, Any] = Field(default_factory=dict)


class ScenarioStatus(BaseModel):
    scenario_id: str
    scenario_type: str
    status: str  # running, completed, stopped
    events_generated: int = 0
    start_time: str | None = None
    end_time: str | None = None


# In-memory store for active scenarios
_active_scenarios: dict[str, dict] = {}


@router.post("/generate")
async def generate_agent_events(request: GenerateAgentEventsRequest):
    """Generate AI Agent behavior events"""
    from behavior_mock.agent_generator import AgentEventGenerator

    generator = AgentEventGenerator()

    if request.agent_id:
        profile = {
            "agent_id": request.agent_id,
            "agent_type": request.agent_type,
            "model": request.model_name,
            "tools": ["web_search", "code_execution", "file_read"],
            "behavior": "assistant",
        }
        events = generator.generate_batch(request.count, profile)
    else:
        events = generator.generate_batch(request.count)

    return {
        "status": "ok",
        "count": len(events),
        "events": events,
    }


@router.post("/scenario/start")
async def start_scenario(request: ScenarioRequest):
    """Start an agent behavior simulation scenario"""
    from behavior_mock.agent_generator import AgentEventGenerator

    generator = AgentEventGenerator()
    scenario_id = f"scenario-{uuid.uuid4().hex[:8]}"

    scenario_map = {
        "normal": lambda: generator.generate_scenario_normal(request.duration_events),
        "loop": lambda: generator.generate_scenario_loop(
            agent_id=request.params.get("agent_id", "agent-stuck-001"),
            loop_count=request.params.get("loop_count", 20),
        ),
        "cost_explosion": lambda: generator.generate_scenario_cost_explosion(
            agent_id=request.params.get("agent_id", "agent-expensive-001"),
            event_count=request.params.get("event_count", 20),
        ),
        "cascading_failure": lambda: generator.generate_scenario_cascading_failure(
            event_count=request.params.get("event_count", 30),
        ),
    }

    if request.scenario not in scenario_map:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario: {request.scenario}. Available: {list(scenario_map.keys())}"
        )

    events = scenario_map[request.scenario]()

    _active_scenarios[scenario_id] = {
        "scenario_id": scenario_id,
        "scenario_type": request.scenario,
        "status": "completed",
        "events_generated": len(events),
        "start_time": datetime.now(UTC).isoformat(),
        "end_time": datetime.now(UTC).isoformat(),
        "events": events,
    }

    return {
        "status": "ok",
        "scenario_id": scenario_id,
        "events_generated": len(events),
        "scenario_type": request.scenario,
    }


@router.get("/scenarios")
async def list_scenarios():
    """List all scenarios"""
    return {
        "scenarios": [
            {
                "scenario_id": s["scenario_id"],
                "scenario_type": s["scenario_type"],
                "status": s["status"],
                "events_generated": s["events_generated"],
            }
            for s in _active_scenarios.values()
        ]
    }


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get scenario details including generated events"""
    if scenario_id not in _active_scenarios:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")

    scenario = _active_scenarios[scenario_id]
    return {
        "scenario_id": scenario["scenario_id"],
        "scenario_type": scenario["scenario_type"],
        "status": scenario["status"],
        "events_generated": scenario["events_generated"],
        "start_time": scenario["start_time"],
        "end_time": scenario["end_time"],
        "events": scenario.get("events", [])[:50],  # Return first 50 events
    }


@router.delete("/scenarios/{scenario_id}")
async def delete_scenario(scenario_id: str):
    """Delete a scenario"""
    if scenario_id not in _active_scenarios:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    del _active_scenarios[scenario_id]
    return {"status": "ok"}


@router.get("/agents")
async def list_available_agents():
    """List all available agent profiles for simulation"""
    from behavior_mock.agent_generator import AGENT_PROFILES
    return {"agents": AGENT_PROFILES}


@router.get("/health")
async def health():
    """Health check for agent mock service"""
    return {
        "status": "ok",
        "service": "agent-mock",
        "active_scenarios": len(_active_scenarios),
    }
