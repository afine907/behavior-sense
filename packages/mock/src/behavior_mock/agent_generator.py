"""
AI Agent行为模拟器
"""
import random
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


# Agent configurations for simulation
AGENT_PROFILES = [
    {
        "agent_id": "agent-researcher-001",
        "agent_type": "llm_agent",
        "model": "claude-3-opus",
        "tools": ["web_search", "file_read", "calculator", "code_execution"],
        "behavior": "research",  # methodical, many tool calls
    },
    {
        "agent_id": "agent-coder-002",
        "agent_type": "llm_agent",
        "model": "gpt-4",
        "tools": ["code_execution", "file_read", "file_write", "terminal"],
        "behavior": "coding",  # heavy code execution
    },
    {
        "agent_id": "agent-analyst-003",
        "agent_type": "workflow_agent",
        "model": "claude-3-sonnet",
        "tools": ["database", "calculator", "visualization"],
        "behavior": "analysis",  # data focused
    },
    {
        "agent_id": "agent-orchestrator-004",
        "agent_type": "multi_agent",
        "model": "gpt-4-turbo",
        "tools": ["delegation", "planning", "monitoring"],
        "behavior": "orchestration",  # delegates to others
    },
    {
        "agent_id": "agent-assistant-005",
        "agent_type": "llm_agent",
        "model": "claude-3-haiku",
        "tools": ["web_search", "calculator", "summary"],
        "behavior": "assistant",  # quick, lightweight
    },
]


class AgentEventGenerator:
    """AI Agent事件生成器"""

    def __init__(self, agent_profiles: list[dict] | None = None):
        self.profiles = agent_profiles or AGENT_PROFILES
        self._active_sessions: dict[str, dict] = {}

    def generate_event(self, agent_profile: dict | None = None) -> dict[str, Any]:
        """生成单个Agent事件"""
        profile = agent_profile or random.choice(self.profiles)
        agent_id = profile["agent_id"]
        behavior = profile["behavior"]

        # Get or create session
        session = self._get_or_create_session(agent_id)

        # Generate event based on behavior pattern
        event_type, properties = self._generate_by_behavior(behavior, profile, session)

        return {
            "event_id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "agent_type": profile["agent_type"],
            "event_type": event_type,
            "timestamp": _utc_now().isoformat(),
            "trace_id": session["trace_id"],
            "session_id": session["session_id"],
            "task_id": session["task_id"],
            "model_name": profile["model"],
            "properties": properties,
            "token_usage": self._generate_token_usage(event_type, profile["model"]),
            "tool_call": self._generate_tool_call(event_type, profile["tools"]) if "tool" in event_type else None,
            "latency_ms": self._generate_latency(event_type),
            "success": self._generate_success(event_type),
        }

    def generate_batch(self, count: int, agent_profile: dict | None = None) -> list[dict]:
        """批量生成事件"""
        return [self.generate_event(agent_profile) for _ in range(count)]

    def generate_scenario_normal(self, duration_events: int = 100) -> list[dict]:
        """正常行为场景 - Agent正常工作"""
        events = []
        for _ in range(duration_events):
            profile = random.choice(self.profiles)
            events.append(self.generate_event(profile))
        return events

    def generate_scenario_loop(self, agent_id: str = "agent-stuck-001",
                                loop_count: int = 20) -> list[dict]:
        """死循环场景 - Agent陷入重复行为"""
        events = []
        tool = random.choice(["web_search", "calculator", "code_execution"])

        for i in range(loop_count):
            events.append({
                "event_id": str(uuid.uuid4()),
                "agent_id": agent_id,
                "agent_type": "llm_agent",
                "event_type": "tool_call",
                "timestamp": _utc_now().isoformat(),
                "trace_id": f"trace-loop-{uuid.uuid4().hex[:8]}",
                "session_id": f"session-loop-{uuid.uuid4().hex[:8]}",
                "model_name": "gpt-4",
                "properties": {"loop_iteration": i, "stuck": True},
                "tool_call": {
                    "tool_name": tool,
                    "tool_type": "search",
                    "latency_ms": random.uniform(100, 500),
                    "success": True,
                },
                "latency_ms": random.uniform(100, 500),
                "success": True,
            })
        return events

    def generate_scenario_cost_explosion(self, agent_id: str = "agent-expensive-001",
                                          event_count: int = 20) -> list[dict]:
        """成本爆炸场景 - Token消耗飙升"""
        events = []
        for i in range(event_count):
            events.append({
                "event_id": str(uuid.uuid4()),
                "agent_id": agent_id,
                "agent_type": "llm_agent",
                "event_type": "llm_request",
                "timestamp": _utc_now().isoformat(),
                "trace_id": f"trace-cost-{uuid.uuid4().hex[:8]}",
                "session_id": f"session-cost-{uuid.uuid4().hex[:8]}",
                "model_name": "gpt-4",
                "properties": {"expensive": True, "iteration": i},
                "token_usage": {
                    "prompt_tokens": random.randint(50000, 200000),
                    "completion_tokens": random.randint(10000, 50000),
                    "total_tokens": 0,  # will be computed
                    "model_name": "gpt-4",
                    "cost_usd": random.uniform(1.0, 10.0),
                },
                "latency_ms": random.uniform(5000, 30000),
                "success": True,
            })
        return events

    def generate_scenario_cascading_failure(self, event_count: int = 30) -> list[dict]:
        """级联失败场景 - 一个Agent失败导致连锁反应"""
        events = []
        agents = [
            {"agent_id": "agent-orchestrator", "agent_type": "multi_agent", "model": "gpt-4"},
            {"agent_id": "agent-worker-1", "agent_type": "llm_agent", "model": "claude-3-sonnet"},
            {"agent_id": "agent-worker-2", "agent_type": "llm_agent", "model": "gpt-4-turbo"},
            {"agent_id": "agent-worker-3", "agent_type": "tool_agent", "model": "claude-3-haiku"},
        ]

        for i in range(event_count):
            # After some normal events, start failures
            is_failure_phase = i > event_count * 0.4

            for agent in agents:
                if is_failure_phase:
                    # Orchestrator times out, workers fail
                    event_type = "timeout" if agent["agent_id"] == "agent-orchestrator" else "error"
                    success = False
                else:
                    event_type = random.choice(["tool_call", "llm_request", "delegation"])
                    success = True

                events.append({
                    "event_id": str(uuid.uuid4()),
                    "agent_id": agent["agent_id"],
                    "agent_type": agent["agent_type"],
                    "event_type": event_type,
                    "timestamp": _utc_now().isoformat(),
                    "trace_id": f"trace-cascade-{i}",
                    "session_id": f"session-cascade-{i}",
                    "model_name": agent["model"],
                    "properties": {"cascade_phase": "failure" if is_failure_phase else "normal"},
                    "latency_ms": random.uniform(100, 500) if success else random.uniform(5000, 30000),
                    "success": success,
                    "error_type": "timeout" if not success else None,
                })
        return events

    def _get_or_create_session(self, agent_id: str) -> dict:
        if agent_id not in self._active_sessions or random.random() < 0.1:
            self._active_sessions[agent_id] = {
                "session_id": f"session-{uuid.uuid4().hex[:12]}",
                "trace_id": f"trace-{uuid.uuid4().hex[:12]}",
                "task_id": f"task-{uuid.uuid4().hex[:12]}",
                "event_count": 0,
            }
        session = self._active_sessions[agent_id]
        session["event_count"] += 1
        return session

    def _generate_by_behavior(self, behavior: str, profile: dict, session: dict) -> tuple[str, dict]:
        if behavior == "research":
            event_type = random.choices(
                ["tool_call", "llm_request", "llm_response", "memory_read", "plan_update"],
                weights=[40, 25, 25, 5, 5],
            )[0]
        elif behavior == "coding":
            event_type = random.choices(
                ["tool_call", "llm_request", "llm_response", "error", "retry"],
                weights=[35, 30, 25, 5, 5],
            )[0]
        elif behavior == "analysis":
            event_type = random.choices(
                ["tool_call", "llm_request", "memory_read", "memory_write", "llm_response"],
                weights=[30, 30, 15, 10, 15],
            )[0]
        elif behavior == "orchestration":
            event_type = random.choices(
                ["delegation", "plan_create", "plan_update", "llm_request", "tool_call"],
                weights=[30, 20, 15, 20, 15],
            )[0]
        else:  # assistant
            event_type = random.choices(
                ["tool_call", "llm_request", "llm_response"],
                weights=[40, 30, 30],
            )[0]

        properties = {"behavior": behavior, "step": random.randint(1, 50)}
        return event_type, properties

    def _generate_token_usage(self, event_type: str, model: str) -> dict | None:
        if event_type not in ("llm_request", "llm_response"):
            return None

        base_prompt = {"gpt-4": 2000, "claude-3-opus": 2500, "claude-3-sonnet": 1500,
                       "claude-3-haiku": 800, "gpt-4-turbo": 1800}.get(model, 1500)
        base_completion = base_prompt // 3

        return {
            "prompt_tokens": base_prompt + random.randint(-500, 2000),
            "completion_tokens": base_completion + random.randint(-200, 1000),
            "total_tokens": 0,
            "cached_tokens": random.randint(0, base_prompt // 2),
            "model_name": model,
            "cost_usd": 0.0,
        }

    def _generate_tool_call(self, event_type: str, tools: list[str]) -> dict | None:
        if event_type != "tool_call":
            return None
        tool = random.choice(tools)
        tool_type_map = {
            "web_search": "search", "file_read": "file_system", "file_write": "file_system",
            "code_execution": "code_execution", "terminal": "code_execution",
            "database": "database", "calculator": "calculation", "visualization": "visualization",
            "delegation": "custom", "planning": "custom", "monitoring": "custom",
            "summary": "custom",
        }
        return {
            "tool_name": tool,
            "tool_type": tool_type_map.get(tool, "custom"),
            "latency_ms": random.uniform(50, 2000),
            "success": random.random() > 0.05,
        }

    def _generate_latency(self, event_type: str) -> float:
        base = {"tool_call": 500, "llm_request": 2000, "llm_response": 500,
                "delegation": 100, "error": 100, "timeout": 30000}.get(event_type, 300)
        return base + random.uniform(-base * 0.3, base * 0.5)

    def _generate_success(self, event_type: str) -> bool:
        if event_type == "error":
            return False
        if event_type == "timeout":
            return False
        return random.random() > 0.05
