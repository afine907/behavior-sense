"""
AI Agent行为异常检测器
"""
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentLoopDetector:
    """死循环检测器 - 检测Agent陷入重复行为模式"""
    # agent_id -> deque of recent (event_type, tool_name, timestamp)
    _agent_history: dict[str, deque] = field(default_factory=lambda: defaultdict(lambda: deque(maxlen=100)))
    # Pattern: same action repeated N times within M seconds
    min_repetitions: int = 5
    window_seconds: int = 60

    def detect(self, agent_id: str, event_type: str, tool_name: str | None = None,
               timestamp: float | None = None) -> dict | None:
        ts = timestamp or time.time()
        history = self._agent_history[agent_id]
        action = f"{event_type}:{tool_name or 'none'}"
        history.append((action, ts))

        # Count same action in window
        cutoff = ts - self.window_seconds
        recent_same = sum(1 for a, t in history if a == action and t >= cutoff)

        if recent_same >= self.min_repetitions:
            return {
                "detector": "loop",
                "agent_id": agent_id,
                "action": action,
                "count": recent_same,
                "window_seconds": self.window_seconds,
                "severity": "high" if recent_same >= self.min_repetitions * 2 else "medium",
            }
        return None


@dataclass
class CostSpikeDetector:
    """成本飙升检测器 - 检测Token消耗异常"""
    # agent_id -> deque of (cost_usd, timestamp)
    _agent_costs: dict[str, deque] = field(default_factory=lambda: defaultdict(lambda: deque(maxlen=1000)))
    # Thresholds
    cost_per_minute_threshold: float = 1.0  # $1/minute
    cost_spike_ratio: float = 5.0  # 5x average
    window_seconds: int = 60

    def detect(self, agent_id: str, cost_usd: float,
               timestamp: float | None = None) -> dict | None:
        ts = timestamp or time.time()
        history = self._agent_costs[agent_id]
        history.append((cost_usd, ts))

        cutoff = ts - self.window_seconds
        recent = [(c, t) for c, t in history if t >= cutoff]
        total_cost = sum(c for c, _ in recent)

        if total_cost > self.cost_per_minute_threshold:
            return {
                "detector": "cost_spike",
                "agent_id": agent_id,
                "total_cost_usd": round(total_cost, 4),
                "threshold": self.cost_per_minute_threshold,
                "event_count": len(recent),
                "severity": "critical" if total_cost > self.cost_per_minute_threshold * 10 else "high",
            }
        return None


@dataclass
class TokenExplosionDetector:
    """Token爆炸检测器 - 检测单次请求Token异常"""
    # Thresholds
    max_prompt_tokens: int = 100000
    max_completion_tokens: int = 50000
    max_total_per_session: int = 1000000
    # agent_id -> session total tokens
    _session_tokens: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def detect(self, agent_id: str, prompt_tokens: int, completion_tokens: int,
               session_id: str | None = None) -> dict | None:
        sid = session_id or agent_id
        total = prompt_tokens + completion_tokens
        self._session_tokens[sid] += total

        alerts = []
        if prompt_tokens > self.max_prompt_tokens:
            alerts.append({
                "type": "prompt_token_explosion",
                "tokens": prompt_tokens,
                "threshold": self.max_prompt_tokens,
            })
        if completion_tokens > self.max_completion_tokens:
            alerts.append({
                "type": "completion_token_explosion",
                "tokens": completion_tokens,
                "threshold": self.max_completion_tokens,
            })
        if self._session_tokens[sid] > self.max_total_per_session:
            alerts.append({
                "type": "session_token_exhaustion",
                "total": self._session_tokens[sid],
                "threshold": self.max_total_per_session,
            })

        if alerts:
            return {
                "detector": "token_explosion",
                "agent_id": agent_id,
                "session_id": sid,
                "alerts": alerts,
                "severity": "high",
            }
        return None


@dataclass
class ToolAbuseDetector:
    """工具滥用检测器 - 检测工具调用频率异常"""
    # agent_id -> deque of (tool_name, timestamp)
    _tool_history: dict[str, deque] = field(default_factory=lambda: defaultdict(lambda: deque(maxlen=500)))
    # Per-tool thresholds
    calls_per_minute: int = 60
    # Dangerous tool patterns
    dangerous_tools: set = field(default_factory=lambda: {"code_execution", "file_system", "database", "network"})
    dangerous_calls_per_minute: int = 10

    def detect(self, agent_id: str, tool_name: str,
               timestamp: float | None = None) -> dict | None:
        ts = timestamp or time.time()
        history = self._tool_history[agent_id]
        history.append((tool_name, ts))

        cutoff = ts - 60
        recent = [(t, ti) for t, ti in history if ti >= cutoff]

        # Check overall tool call rate
        if len(recent) > self.calls_per_minute:
            return {
                "detector": "tool_abuse",
                "agent_id": agent_id,
                "tool_name": tool_name,
                "calls_per_minute": len(recent),
                "threshold": self.calls_per_minute,
                "severity": "medium",
            }

        # Check dangerous tool rate
        if tool_name in self.dangerous_tools:
            dangerous_count = sum(1 for t, _ in recent if t in self.dangerous_tools)
            if dangerous_count > self.dangerous_calls_per_minute:
                return {
                    "detector": "dangerous_tool_abuse",
                    "agent_id": agent_id,
                    "tool_name": tool_name,
                    "dangerous_calls_per_minute": dangerous_count,
                    "threshold": self.dangerous_calls_per_minute,
                    "severity": "high",
                }
        return None


@dataclass
class TimeoutCascadeDetector:
    """超时级联检测器 - 检测Agent超时导致的级联效应"""
    # agent_id -> deque of (is_timeout, timestamp)
    _timeout_history: dict[str, deque] = field(default_factory=lambda: defaultdict(lambda: deque(maxlen=100)))
    # Thresholds
    timeout_count_threshold: int = 3
    window_seconds: int = 300  # 5 minutes
    cascade_depth_threshold: int = 2  # delegation chain depth

    def detect(self, agent_id: str, is_timeout: bool,
               delegation_depth: int = 0,
               timestamp: float | None = None) -> dict | None:
        if not is_timeout:
            return None

        ts = timestamp or time.time()
        history = self._timeout_history[agent_id]
        history.append((True, ts))

        cutoff = ts - self.window_seconds
        recent_timeouts = sum(1 for _, t in history if t >= cutoff)

        if recent_timeouts >= self.timeout_count_threshold:
            return {
                "detector": "timeout_cascade",
                "agent_id": agent_id,
                "timeout_count": recent_timeouts,
                "threshold": self.timeout_count_threshold,
                "delegation_depth": delegation_depth,
                "severity": "critical" if delegation_depth >= self.cascade_depth_threshold else "high",
            }
        return None


@dataclass
class CapabilityDriftDetector:
    """能力漂移检测器 - 检测Agent行为偏离预期能力"""
    # agent_id -> baseline capability profile
    _baselines: dict[str, dict] = field(default_factory=dict)
    # Drift thresholds
    error_rate_threshold: float = 0.3  # 30% error rate = drift
    latency_drift_ratio: float = 3.0  # 3x baseline latency = drift
    min_samples: int = 20

    def set_baseline(self, agent_id: str, avg_latency: float, error_rate: float,
                     typical_tools: list[str]) -> None:
        self._baselines[agent_id] = {
            "avg_latency": avg_latency,
            "error_rate": error_rate,
            "typical_tools": set(typical_tools),
        }

    def detect(self, agent_id: str, current_latency: float, is_error: bool,
               tool_name: str | None = None) -> dict | None:
        baseline = self._baselines.get(agent_id)
        if not baseline:
            return None

        issues = []

        # Check latency drift
        if baseline["avg_latency"] > 0 and current_latency > baseline["avg_latency"] * self.latency_drift_ratio:
            issues.append({
                "type": "latency_drift",
                "current": current_latency,
                "baseline": baseline["avg_latency"],
                "ratio": current_latency / baseline["avg_latency"],
            })

        # Check tool usage drift
        if tool_name and tool_name not in baseline["typical_tools"]:
            issues.append({
                "type": "tool_drift",
                "unexpected_tool": tool_name,
                "typical_tools": list(baseline["typical_tools"]),
            })

        if issues:
            return {
                "detector": "capability_drift",
                "agent_id": agent_id,
                "issues": issues,
                "severity": "medium",
            }
        return None


@dataclass
class MultiAgentContentionDetector:
    """多Agent资源竞争检测器"""
    # resource -> deque of (agent_id, timestamp, action)
    _resource_history: dict[str, deque] = field(default_factory=lambda: defaultdict(lambda: deque(maxlen=200)))
    # Thresholds
    contention_agent_threshold: int = 3  # N agents accessing same resource
    window_seconds: int = 10

    def detect(self, agent_id: str, resource_id: str, action: str = "access",
               timestamp: float | None = None) -> dict | None:
        ts = timestamp or time.time()
        history = self._resource_history[resource_id]
        history.append((agent_id, ts, action))

        cutoff = ts - self.window_seconds
        recent = [(a, t, act) for a, t, act in history if t >= cutoff]
        unique_agents = set(a for a, _, _ in recent)

        if len(unique_agents) >= self.contention_agent_threshold:
            return {
                "detector": "resource_contention",
                "resource_id": resource_id,
                "agents": list(unique_agents),
                "access_count": len(recent),
                "window_seconds": self.window_seconds,
                "severity": "medium",
            }
        return None


class AgentAnomalyDetectorSet:
    """Agent异常检测器集合 - 聚合所有检测器"""

    def __init__(self):
        self.loop_detector = AgentLoopDetector()
        self.cost_spike = CostSpikeDetector()
        self.token_explosion = TokenExplosionDetector()
        self.tool_abuse = ToolAbuseDetector()
        self.timeout_cascade = TimeoutCascadeDetector()
        self.capability_drift = CapabilityDriftDetector()
        self.resource_contention = MultiAgentContentionDetector()

    def detect_all(self, event_data: dict[str, Any]) -> list[dict]:
        """对一个Agent事件运行所有检测器"""
        alerts = []
        agent_id = event_data.get("agent_id", "unknown")
        event_type = event_data.get("event_type", "unknown")
        ts = event_data.get("timestamp")

        # Loop detection
        result = self.loop_detector.detect(
            agent_id, event_type,
            tool_name=event_data.get("tool_name"),
            timestamp=ts,
        )
        if result:
            alerts.append(result)

        # Cost spike detection
        cost = event_data.get("cost_usd", 0)
        if cost > 0:
            result = self.cost_spike.detect(agent_id, cost, timestamp=ts)
            if result:
                alerts.append(result)

        # Token explosion detection
        prompt_tokens = event_data.get("prompt_tokens", 0)
        completion_tokens = event_data.get("completion_tokens", 0)
        if prompt_tokens > 0 or completion_tokens > 0:
            result = self.token_explosion.detect(
                agent_id, prompt_tokens, completion_tokens,
                session_id=event_data.get("session_id"),
            )
            if result:
                alerts.append(result)

        # Tool abuse detection
        tool_name = event_data.get("tool_name")
        if tool_name:
            result = self.tool_abuse.detect(agent_id, tool_name, timestamp=ts)
            if result:
                alerts.append(result)

        # Timeout cascade detection
        is_timeout = event_data.get("event_type") == "timeout"
        if is_timeout:
            result = self.timeout_cascade.detect(
                agent_id, True,
                delegation_depth=event_data.get("delegation_depth", 0),
                timestamp=ts,
            )
            if result:
                alerts.append(result)

        # Capability drift detection
        latency = event_data.get("latency_ms", 0)
        if latency > 0:
            result = self.capability_drift.detect(
                agent_id, latency,
                is_error=event_data.get("success") is False,
                tool_name=tool_name,
            )
            if result:
                alerts.append(result)

        # Resource contention detection
        resource_id = event_data.get("resource_id")
        if resource_id:
            result = self.resource_contention.detect(
                agent_id, resource_id,
                action=event_data.get("resource_action", "access"),
                timestamp=ts,
            )
            if result:
                alerts.append(result)

        return alerts
