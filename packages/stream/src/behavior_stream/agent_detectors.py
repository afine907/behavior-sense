"""
AI Agent行为异常检测器

Hardened with thread safety, memory bounds, input validation,
graceful degradation, and per-detector metrics collection.
"""
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Maximum number of sessions tracked by TokenExplosionDetector to prevent
# unbounded memory growth when session IDs are unique per request.
_MAX_SESSION_TRACKED: int = 10_000


def _avg_ms(total_ms: float, count: int) -> float:
    """Compute average ms per detection, avoiding division by zero."""
    denom = count + (1 if total_ms > 0 else 0)
    return round(total_ms / max(denom, 1), 3)


@dataclass
class AgentLoopDetector:
    """死循环检测器 - 检测Agent陷入重复行为模式"""
    # agent_id -> deque of recent (action, timestamp)
    _agent_history: dict[str, deque] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=100))
    )
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _detect_count: int = field(default=0, init=False, repr=False)
    _detect_total_ms: float = field(default=0.0, init=False, repr=False)
    # Pattern: same action repeated N times within M seconds
    min_repetitions: int = 5
    window_seconds: int = 60

    def detect(self, agent_id: str, event_type: str, tool_name: str | None = None,
               timestamp: float | None = None) -> dict | None:
        """检测循环模式"""
        # Input validation
        if not agent_id or not event_type:
            return None

        t0 = time.monotonic()
        try:
            ts = timestamp if timestamp is not None and timestamp > 0 else time.time()
            action = f"{event_type}:{tool_name or 'none'}"

            with self._lock:
                history = self._agent_history[agent_id]
                history.append((action, ts))

                # Count same action in window
                cutoff = ts - self.window_seconds
                recent_same = sum(1 for a, t in history if a == action and t >= cutoff)

            if recent_same >= self.min_repetitions:
                self._detect_count += 1
                return {
                    "detector": "loop",
                    "agent_id": agent_id,
                    "action": action,
                    "count": recent_same,
                    "window_seconds": self.window_seconds,
                    "severity": "high" if recent_same >= self.min_repetitions * 2 else "medium",
                    "detected_at": ts,
                }
            return None
        except Exception:
            logger.exception("AgentLoopDetector.detect failed for agent_id=%s", agent_id)
            return None
        finally:
            self._detect_total_ms += (time.monotonic() - t0) * 1000

    def get_stats(self) -> dict:
        """获取检测器统计"""
        with self._lock:
            tracked = len(self._agent_history)
        return {
            "detector": "loop",
            "detection_count": self._detect_count,
            "tracked_agents": tracked,
            "avg_detect_ms": _avg_ms(
                self._detect_total_ms, self._detect_count
            ),
        }


@dataclass
class CostSpikeDetector:
    """成本飙升检测器 - 检测Token消耗异常"""
    # agent_id -> deque of (cost_usd, timestamp)
    _agent_costs: dict[str, deque] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=1000))
    )
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _detect_count: int = field(default=0, init=False, repr=False)
    _detect_total_ms: float = field(default=0.0, init=False, repr=False)
    # Thresholds
    cost_per_minute_threshold: float = 1.0  # $1/minute
    cost_spike_ratio: float = 5.0  # 5x average
    window_seconds: int = 60

    def detect(self, agent_id: str, cost_usd: float,
               timestamp: float | None = None) -> dict | None:
        """检测成本飙升"""
        # Input validation
        if not agent_id:
            return None
        if not isinstance(cost_usd, (int, float)) or cost_usd < 0:
            return None

        t0 = time.monotonic()
        try:
            ts = timestamp if timestamp is not None and timestamp > 0 else time.time()

            with self._lock:
                history = self._agent_costs[agent_id]
                history.append((cost_usd, ts))

                cutoff = ts - self.window_seconds
                recent = [(c, t) for c, t in history if t >= cutoff]
                total_cost = sum(c for c, _ in recent)

            if total_cost > self.cost_per_minute_threshold:
                self._detect_count += 1
                return {
                    "detector": "cost_spike",
                    "agent_id": agent_id,
                    "total_cost_usd": round(total_cost, 4),
                    "threshold": self.cost_per_minute_threshold,
                    "event_count": len(recent),
                    "severity": (
                        "critical"
                        if total_cost > self.cost_per_minute_threshold * 10
                        else "high"
                    ),
                    "detected_at": ts,
                }
            return None
        except Exception:
            logger.exception("CostSpikeDetector.detect failed for agent_id=%s", agent_id)
            return None
        finally:
            self._detect_total_ms += (time.monotonic() - t0) * 1000

    def get_stats(self) -> dict:
        """获取检测器统计"""
        with self._lock:
            tracked = len(self._agent_costs)
        return {
            "detector": "cost_spike",
            "detection_count": self._detect_count,
            "tracked_agents": tracked,
            "avg_detect_ms": _avg_ms(
                self._detect_total_ms, self._detect_count
            ),
        }


@dataclass
class TokenExplosionDetector:
    """Token爆炸检测器 - 检测单次请求Token异常"""
    # Thresholds
    max_prompt_tokens: int = 100000
    max_completion_tokens: int = 50000
    max_total_per_session: int = 1000000
    # agent_id -> session total tokens
    _session_tokens: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _session_order: deque = field(default_factory=lambda: deque(maxlen=_MAX_SESSION_TRACKED))
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _detect_count: int = field(default=0, init=False, repr=False)
    _detect_total_ms: float = field(default=0.0, init=False, repr=False)

    def detect(self, agent_id: str, prompt_tokens: int, completion_tokens: int,
               session_id: str | None = None) -> dict | None:
        """检测Token爆炸"""
        # Input validation
        if not agent_id:
            return None
        if not isinstance(prompt_tokens, (int, float)) or prompt_tokens < 0:
            prompt_tokens = 0
        if not isinstance(completion_tokens, (int, float)) or completion_tokens < 0:
            completion_tokens = 0

        t0 = time.monotonic()
        try:
            sid = session_id or agent_id
            total = prompt_tokens + completion_tokens

            with self._lock:
                # Evict oldest sessions if we hit the cap
                is_new = sid not in self._session_tokens
                at_cap = len(self._session_tokens) >= _MAX_SESSION_TRACKED
                if is_new and at_cap:
                    evict_sid = self._session_order.popleft()
                    self._session_tokens.pop(evict_sid, None)

                self._session_tokens[sid] += total
                self._session_order.append(sid)
                session_total = self._session_tokens[sid]

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
            if session_total > self.max_total_per_session:
                alerts.append({
                    "type": "session_token_exhaustion",
                    "total": session_total,
                    "threshold": self.max_total_per_session,
                })

            if alerts:
                self._detect_count += 1
                return {
                    "detector": "token_explosion",
                    "agent_id": agent_id,
                    "session_id": sid,
                    "alerts": alerts,
                    "severity": "high",
                    "detected_at": time.time(),
                }
            return None
        except Exception:
            logger.exception("TokenExplosionDetector.detect failed for agent_id=%s", agent_id)
            return None
        finally:
            self._detect_total_ms += (time.monotonic() - t0) * 1000

    def get_stats(self) -> dict:
        """获取检测器统计"""
        with self._lock:
            tracked = len(self._session_tokens)
        return {
            "detector": "token_explosion",
            "detection_count": self._detect_count,
            "tracked_sessions": tracked,
            "avg_detect_ms": _avg_ms(
                self._detect_total_ms, self._detect_count
            ),
        }


@dataclass
class ToolAbuseDetector:
    """工具滥用检测器 - 检测工具调用频率异常"""
    # agent_id -> deque of (tool_name, timestamp)
    _tool_history: dict[str, deque] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=500))
    )
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _detect_count: int = field(default=0, init=False, repr=False)
    _detect_total_ms: float = field(default=0.0, init=False, repr=False)
    # Per-tool thresholds
    calls_per_minute: int = 60
    # Dangerous tool patterns
    dangerous_tools: set = field(
        default_factory=lambda: {"code_execution", "file_system", "database", "network"}
    )
    dangerous_calls_per_minute: int = 10

    def detect(self, agent_id: str, tool_name: str,
               timestamp: float | None = None) -> dict | None:
        """检测工具滥用"""
        # Input validation
        if not agent_id or not tool_name:
            return None

        t0 = time.monotonic()
        try:
            ts = timestamp if timestamp is not None and timestamp > 0 else time.time()

            with self._lock:
                history = self._tool_history[agent_id]
                history.append((tool_name, ts))

                cutoff = ts - 60
                recent = [(t, ti) for t, ti in history if ti >= cutoff]

            # Check overall tool call rate
            if len(recent) > self.calls_per_minute:
                self._detect_count += 1
                return {
                    "detector": "tool_abuse",
                    "agent_id": agent_id,
                    "tool_name": tool_name,
                    "calls_per_minute": len(recent),
                    "threshold": self.calls_per_minute,
                    "severity": "medium",
                    "detected_at": ts,
                }

            # Check dangerous tool rate
            if tool_name in self.dangerous_tools:
                dangerous_count = sum(1 for t, _ in recent if t in self.dangerous_tools)
                if dangerous_count > self.dangerous_calls_per_minute:
                    self._detect_count += 1
                    return {
                        "detector": "dangerous_tool_abuse",
                        "agent_id": agent_id,
                        "tool_name": tool_name,
                        "dangerous_calls_per_minute": dangerous_count,
                        "threshold": self.dangerous_calls_per_minute,
                        "severity": "high",
                        "detected_at": ts,
                    }
            return None
        except Exception:
            logger.exception("ToolAbuseDetector.detect failed for agent_id=%s", agent_id)
            return None
        finally:
            self._detect_total_ms += (time.monotonic() - t0) * 1000

    def get_stats(self) -> dict:
        """获取检测器统计"""
        with self._lock:
            tracked = len(self._tool_history)
        return {
            "detector": "tool_abuse",
            "detection_count": self._detect_count,
            "tracked_agents": tracked,
            "avg_detect_ms": _avg_ms(
                self._detect_total_ms, self._detect_count
            ),
        }


@dataclass
class TimeoutCascadeDetector:
    """超时级联检测器 - 检测Agent超时导致的级联效应"""
    # agent_id -> deque of (is_timeout, timestamp)
    _timeout_history: dict[str, deque] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=100))
    )
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _detect_count: int = field(default=0, init=False, repr=False)
    _detect_total_ms: float = field(default=0.0, init=False, repr=False)
    # Thresholds
    timeout_count_threshold: int = 3
    window_seconds: int = 300  # 5 minutes
    cascade_depth_threshold: int = 2  # delegation chain depth

    def detect(self, agent_id: str, is_timeout: bool,
               delegation_depth: int = 0,
               timestamp: float | None = None) -> dict | None:
        """检测超时级联"""
        if not is_timeout:
            return None

        # Input validation
        if not agent_id:
            return None
        if not isinstance(delegation_depth, (int, float)) or delegation_depth < 0:
            delegation_depth = 0

        t0 = time.monotonic()
        try:
            ts = timestamp if timestamp is not None and timestamp > 0 else time.time()

            with self._lock:
                history = self._timeout_history[agent_id]
                history.append((True, ts))

                cutoff = ts - self.window_seconds
                recent_timeouts = sum(1 for _, t in history if t >= cutoff)

            if recent_timeouts >= self.timeout_count_threshold:
                self._detect_count += 1
                return {
                    "detector": "timeout_cascade",
                    "agent_id": agent_id,
                    "timeout_count": recent_timeouts,
                    "threshold": self.timeout_count_threshold,
                    "delegation_depth": delegation_depth,
                    "severity": (
                        "critical"
                        if delegation_depth >= self.cascade_depth_threshold
                        else "high"
                    ),
                    "detected_at": ts,
                }
            return None
        except Exception:
            logger.exception("TimeoutCascadeDetector.detect failed for agent_id=%s", agent_id)
            return None
        finally:
            self._detect_total_ms += (time.monotonic() - t0) * 1000

    def get_stats(self) -> dict:
        """获取检测器统计"""
        with self._lock:
            tracked = len(self._timeout_history)
        return {
            "detector": "timeout_cascade",
            "detection_count": self._detect_count,
            "tracked_agents": tracked,
            "avg_detect_ms": _avg_ms(
                self._detect_total_ms, self._detect_count
            ),
        }


@dataclass
class CapabilityDriftDetector:
    """能力漂移检测器 - 检测Agent行为偏离预期能力"""
    # agent_id -> baseline capability profile
    _baselines: dict[str, dict] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _detect_count: int = field(default=0, init=False, repr=False)
    _detect_total_ms: float = field(default=0.0, init=False, repr=False)
    # Drift thresholds
    error_rate_threshold: float = 0.3  # 30% error rate = drift
    latency_drift_ratio: float = 3.0  # 3x baseline latency = drift
    min_samples: int = 20

    def set_baseline(self, agent_id: str, avg_latency: float, error_rate: float,
                     typical_tools: list[str]) -> None:
        """设置Agent基线能力画像"""
        if not agent_id:
            return
        # Validate inputs
        if not isinstance(avg_latency, (int, float)) or avg_latency < 0:
            avg_latency = 0.0
        if not isinstance(error_rate, (int, float)):
            error_rate = 0.0
        if not isinstance(typical_tools, (list, set)):
            typical_tools = []

        with self._lock:
            self._baselines[agent_id] = {
                "avg_latency": float(avg_latency),
                "error_rate": float(error_rate),
                "typical_tools": set(typical_tools),
            }

    def detect(self, agent_id: str, current_latency: float, is_error: bool,
               tool_name: str | None = None) -> dict | None:
        """检测能力漂移"""
        # Input validation
        if not agent_id:
            return None
        if not isinstance(current_latency, (int, float)) or current_latency < 0:
            current_latency = 0.0

        t0 = time.monotonic()
        try:
            with self._lock:
                baseline = self._baselines.get(agent_id)
                if not baseline:
                    return None
                # Snapshot baseline under lock to avoid TOCTOU
                avg_latency = baseline["avg_latency"]
                typical_tools = set(baseline["typical_tools"])

            issues = []

            # Check latency drift
            if avg_latency > 0 and current_latency > avg_latency * self.latency_drift_ratio:
                issues.append({
                    "type": "latency_drift",
                    "current": current_latency,
                    "baseline": avg_latency,
                    "ratio": round(current_latency / avg_latency, 2),
                })

            # Check tool usage drift
            if tool_name and tool_name not in typical_tools:
                issues.append({
                    "type": "tool_drift",
                    "unexpected_tool": tool_name,
                    "typical_tools": sorted(typical_tools),
                })

            if issues:
                self._detect_count += 1
                return {
                    "detector": "capability_drift",
                    "agent_id": agent_id,
                    "issues": issues,
                    "severity": "medium",
                    "detected_at": time.time(),
                }
            return None
        except Exception:
            logger.exception("CapabilityDriftDetector.detect failed for agent_id=%s", agent_id)
            return None
        finally:
            self._detect_total_ms += (time.monotonic() - t0) * 1000

    def get_stats(self) -> dict:
        """获取检测器统计"""
        with self._lock:
            tracked = len(self._baselines)
        return {
            "detector": "capability_drift",
            "detection_count": self._detect_count,
            "tracked_baselines": tracked,
            "avg_detect_ms": _avg_ms(
                self._detect_total_ms, self._detect_count
            ),
        }


@dataclass
class MultiAgentContentionDetector:
    """多Agent资源竞争检测器"""
    # resource -> deque of (agent_id, timestamp, action)
    _resource_history: dict[str, deque] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=200))
    )
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _detect_count: int = field(default=0, init=False, repr=False)
    _detect_total_ms: float = field(default=0.0, init=False, repr=False)
    # Thresholds
    contention_agent_threshold: int = 3  # N agents accessing same resource
    window_seconds: int = 10

    def detect(self, agent_id: str, resource_id: str, action: str = "access",
               timestamp: float | None = None) -> dict | None:
        """检测资源竞争"""
        # Input validation
        if not agent_id or not resource_id:
            return None

        t0 = time.monotonic()
        try:
            ts = timestamp if timestamp is not None and timestamp > 0 else time.time()

            with self._lock:
                history = self._resource_history[resource_id]
                history.append((agent_id, ts, action))

                cutoff = ts - self.window_seconds
                recent = [(a, t, act) for a, t, act in history if t >= cutoff]
                unique_agents = set(a for a, _, _ in recent)

            if len(unique_agents) >= self.contention_agent_threshold:
                self._detect_count += 1
                return {
                    "detector": "resource_contention",
                    "resource_id": resource_id,
                    "agents": sorted(unique_agents),
                    "access_count": len(recent),
                    "window_seconds": self.window_seconds,
                    "severity": "medium",
                    "detected_at": ts,
                }
            return None
        except Exception:
            logger.exception(
                "MultiAgentContentionDetector.detect failed for agent_id=%s, resource_id=%s",
                agent_id, resource_id,
            )
            return None
        finally:
            self._detect_total_ms += (time.monotonic() - t0) * 1000

    def get_stats(self) -> dict:
        """获取检测器统计"""
        with self._lock:
            tracked = len(self._resource_history)
        return {
            "detector": "resource_contention",
            "detection_count": self._detect_count,
            "tracked_resources": tracked,
            "avg_detect_ms": _avg_ms(
                self._detect_total_ms, self._detect_count
            ),
        }


@dataclass
class PromptInjectionDetector:
    """Prompt Injection检测器 - 检测Agent输入中的提示注入攻击"""
    # agent_id -> deque of (input_text, timestamp, score)
    _input_history: dict[str, deque] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=200))
    )
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _detect_count: int = field(default=0, init=False, repr=False)
    _detect_total_ms: float = field(default=0.0, init=False, repr=False)
    # Injection indicator patterns (lowercase substrings)
    injection_indicators: set = field(
        default_factory=lambda: {
            "ignore previous", "ignore above", "disregard prior",
            "forget your instructions", "new instructions:",
            "system prompt", "you are now", "act as",
            "override", "jailbreak", "do anything now",
            "no restrictions", "bypass", "reveal your prompt",
        }
    )
    # Threshold: minimum indicator matches before alerting
    min_indicators: int = 2
    # Threshold: number of suspicious inputs from same agent in window
    suspicious_input_threshold: int = 3
    window_seconds: int = 300  # 5 minutes

    def _score_input(self, text: str) -> tuple[float, list[str]]:
        """Score an input text for injection likelihood. Returns (score, matched_indicators)."""
        if not text:
            return 0.0, []
        lower = text.lower()
        matches = [ind for ind in self.injection_indicators if ind in lower]
        score = len(matches) / max(len(self.injection_indicators), 1)
        return score, matches

    def detect(self, agent_id: str, input_text: str,
               timestamp: float | None = None) -> dict | None:
        """检测prompt injection"""
        if not agent_id or not input_text:
            return None

        t0 = time.monotonic()
        try:
            ts = timestamp if timestamp is not None and timestamp > 0 else time.time()
            score, matches = self._score_input(input_text)

            if score > 0:
                with self._lock:
                    self._input_history[agent_id].append((input_text, ts, score))
                    cutoff = ts - self.window_seconds
                    recent_suspicious = sum(
                        1 for _, t, _ in self._input_history[agent_id] if t >= cutoff
                    )

                if len(matches) >= self.min_indicators or recent_suspicious >= self.suspicious_input_threshold:
                    self._detect_count += 1
                    return {
                        "detector": "prompt_injection",
                        "agent_id": agent_id,
                        "matched_indicators": matches,
                        "suspicion_score": round(score, 3),
                        "recent_suspicious_count": recent_suspicious,
                        "severity": "critical" if len(matches) >= self.min_indicators * 2 else "high",
                        "detected_at": ts,
                    }
            return None
        except Exception:
            logger.exception("PromptInjectionDetector.detect failed for agent_id=%s", agent_id)
            return None
        finally:
            self._detect_total_ms += (time.monotonic() - t0) * 1000

    def get_stats(self) -> dict:
        """获取检测器统计"""
        with self._lock:
            tracked = len(self._input_history)
        return {
            "detector": "prompt_injection",
            "detection_count": self._detect_count,
            "tracked_agents": tracked,
            "avg_detect_ms": _avg_ms(
                self._detect_total_ms, self._detect_count
            ),
        }


@dataclass
class DataExfiltrationDetector:
    """数据窃取检测器 - 检测通过工具输出的潜在数据泄露"""
    # agent_id -> deque of (output_size, has_sensitive, timestamp)
    _output_history: dict[str, deque] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=500))
    )
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _detect_count: int = field(default=0, init=False, repr=False)
    _detect_total_ms: float = field(default=0.0, init=False, repr=False)
    # Sensitive data indicators in tool output
    sensitive_patterns: set = field(
        default_factory=lambda: {
            "password", "secret", "api_key", "token", "credential",
            "private_key", "access_key", "ssn", "credit_card",
            "bearer", "authorization", "connection_string",
        }
    )
    # Thresholds
    max_output_bytes_per_window: int = 1_000_000  # 1 MB per window
    max_sensitive_outputs_per_window: int = 5
    window_seconds: int = 300  # 5 minutes

    def _check_sensitive(self, output_text: str) -> bool:
        """Check if output text contains sensitive data indicators."""
        if not output_text:
            return False
        lower = output_text.lower()
        return any(pat in lower for pat in self.sensitive_patterns)

    def detect(self, agent_id: str, tool_name: str, output_text: str = "",
               output_size_bytes: int = 0,
               timestamp: float | None = None) -> dict | None:
        """检测数据窃取"""
        if not agent_id:
            return None
        if not isinstance(output_size_bytes, (int, float)) or output_size_bytes < 0:
            output_size_bytes = len(output_text.encode("utf-8")) if output_text else 0

        t0 = time.monotonic()
        try:
            ts = timestamp if timestamp is not None and timestamp > 0 else time.time()
            has_sensitive = self._check_sensitive(output_text)

            with self._lock:
                history = self._output_history[agent_id]
                history.append((output_size_bytes, has_sensitive, ts))

                cutoff = ts - self.window_seconds
                recent = [(s, sen, t) for s, sen, t in history if t >= cutoff]
                total_bytes = sum(s for s, _, _ in recent)
                sensitive_count = sum(1 for _, sen, _ in recent if sen)

            alerts = []
            if total_bytes > self.max_output_bytes_per_window:
                alerts.append({
                    "type": "excessive_output_volume",
                    "total_bytes": total_bytes,
                    "threshold_bytes": self.max_output_bytes_per_window,
                })
            if sensitive_count >= self.max_sensitive_outputs_per_window:
                alerts.append({
                    "type": "sensitive_data_leak",
                    "sensitive_output_count": sensitive_count,
                    "threshold": self.max_sensitive_outputs_per_window,
                })

            if alerts:
                self._detect_count += 1
                return {
                    "detector": "data_exfiltration",
                    "agent_id": agent_id,
                    "tool_name": tool_name,
                    "alerts": alerts,
                    "severity": "critical" if sensitive_count >= self.max_sensitive_outputs_per_window else "high",
                    "detected_at": ts,
                }
            return None
        except Exception:
            logger.exception("DataExfiltrationDetector.detect failed for agent_id=%s", agent_id)
            return None
        finally:
            self._detect_total_ms += (time.monotonic() - t0) * 1000

    def get_stats(self) -> dict:
        """获取检测器统计"""
        with self._lock:
            tracked = len(self._output_history)
        return {
            "detector": "data_exfiltration",
            "detection_count": self._detect_count,
            "tracked_agents": tracked,
            "avg_detect_ms": _avg_ms(
                self._detect_total_ms, self._detect_count
            ),
        }


@dataclass
class HallucinationDetector:
    """幻觉检测器 - 检测Agent输出中的潜在幻觉"""
    # agent_id -> deque of (confidence, citation_count, timestamp)
    _output_history: dict[str, deque] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=200))
    )
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _detect_count: int = field(default=0, init=False, repr=False)
    _detect_total_ms: float = field(default=0.0, init=False, repr=False)
    # Hallucination indicators
    hallucination_phrases: set = field(
        default_factory=lambda: {
            "i'm not sure but", "i think it might", "i believe",
            "it's possible that", "as far as i know",
            "i don't have access to", "i cannot verify",
            "this may not be accurate", "please verify",
        }
    )
    # Thresholds
    min_confidence: float = 0.3  # Below this = suspiciously low confidence
    min_citation_ratio: float = 0.1  # Below this = too few citations
    min_hallucination_phrases: int = 2
    low_confidence_streak_threshold: int = 3

    def detect(self, agent_id: str, output_text: str = "",
               confidence: float = 1.0, citation_count: int = 0,
               source_count: int = 0,
               timestamp: float | None = None) -> dict | None:
        """检测幻觉"""
        if not agent_id:
            return None
        if not isinstance(confidence, (int, float)):
            confidence = 1.0
        confidence = max(0.0, min(1.0, confidence))

        t0 = time.monotonic()
        try:
            ts = timestamp if timestamp is not None and timestamp > 0 else time.time()

            # Count hallucination indicator phrases
            lower = (output_text or "").lower()
            phrase_matches = [p for p in self.hallucination_phrases if p in lower]

            # Compute citation ratio
            citation_ratio = citation_count / max(source_count, 1) if source_count > 0 else 0.0

            with self._lock:
                history = self._output_history[agent_id]
                history.append((confidence, citation_count, ts))

                # Count consecutive low-confidence outputs
                recent = [(c, _, t) for c, _, t in history if t >= ts - 60]
                low_conf_streak = 0
                for c, _, _ in reversed(recent):
                    if c < self.min_confidence:
                        low_conf_streak += 1
                    else:
                        break

            alerts = []
            if len(phrase_matches) >= self.min_hallucination_phrases:
                alerts.append({
                    "type": "hedging_language",
                    "matched_phrases": phrase_matches,
                    "count": len(phrase_matches),
                })
            if confidence < self.min_confidence:
                alerts.append({
                    "type": "low_confidence",
                    "confidence": round(confidence, 3),
                    "threshold": self.min_confidence,
                })
            if source_count > 0 and citation_ratio < self.min_citation_ratio:
                alerts.append({
                    "type": "insufficient_citations",
                    "citation_ratio": round(citation_ratio, 3),
                    "threshold": self.min_citation_ratio,
                })
            if low_conf_streak >= self.low_confidence_streak_threshold:
                alerts.append({
                    "type": "repeated_low_confidence",
                    "streak_length": low_conf_streak,
                    "threshold": self.low_confidence_streak_threshold,
                })

            if alerts:
                self._detect_count += 1
                return {
                    "detector": "hallucination",
                    "agent_id": agent_id,
                    "alerts": alerts,
                    "severity": "high" if len(alerts) >= 2 else "medium",
                    "detected_at": ts,
                }
            return None
        except Exception:
            logger.exception("HallucinationDetector.detect failed for agent_id=%s", agent_id)
            return None
        finally:
            self._detect_total_ms += (time.monotonic() - t0) * 1000

    def get_stats(self) -> dict:
        """获取检测器统计"""
        with self._lock:
            tracked = len(self._output_history)
        return {
            "detector": "hallucination",
            "detection_count": self._detect_count,
            "tracked_agents": tracked,
            "avg_detect_ms": _avg_ms(
                self._detect_total_ms, self._detect_count
            ),
        }


@dataclass
class CostExplosionDetector:
    """成本爆炸检测器 - 检测整个Agent舰队的突然成本飙升"""
    # agent_id -> deque of (cost_usd, model, timestamp)
    _fleet_costs: dict[str, deque] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=1000))
    )
    # Global fleet-level aggregates
    _fleet_total_recent: float = field(default=0.0)
    _fleet_baseline_window: deque = field(
        default_factory=lambda: deque(maxlen=100)
    )
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _detect_count: int = field(default=0, init=False, repr=False)
    _detect_total_ms: float = field(default=0.0, init=False, repr=False)
    # Thresholds
    per_agent_per_minute_limit: float = 2.0  # $2/agent/minute
    fleet_per_minute_limit: float = 50.0  # $50 total fleet/minute
    explosion_ratio: float = 10.0  # 10x baseline
    window_seconds: int = 60
    min_agents_for_fleet_alert: int = 2

    def detect(self, agent_id: str, cost_usd: float, model: str = "",
               timestamp: float | None = None) -> dict | None:
        """检测成本爆炸（单Agent + 舰队级别）"""
        if not agent_id:
            return None
        if not isinstance(cost_usd, (int, float)) or cost_usd < 0:
            return None

        t0 = time.monotonic()
        try:
            ts = timestamp if timestamp is not None and timestamp > 0 else time.time()

            with self._lock:
                self._fleet_costs[agent_id].append((cost_usd, model, ts))

                cutoff = ts - self.window_seconds

                # Per-agent aggregation
                agent_history = self._fleet_costs[agent_id]
                agent_recent = [(c, t) for c, _, t in agent_history if t >= cutoff]
                agent_total = sum(c for c, _ in agent_recent)

                # Fleet-wide aggregation
                fleet_total = 0.0
                fleet_agent_set: set[str] = set()
                for aid, history in self._fleet_costs.items():
                    for c, _, t in history:
                        if t >= cutoff:
                            fleet_total += c
                            fleet_agent_set.add(aid)

            alerts = []

            # Per-agent explosion
            if agent_total > self.per_agent_per_minute_limit:
                alerts.append({
                    "type": "agent_cost_explosion",
                    "agent_id": agent_id,
                    "agent_total_usd": round(agent_total, 4),
                    "limit_usd": self.per_agent_per_minute_limit,
                })

            # Fleet-wide explosion
            if (fleet_total > self.fleet_per_minute_limit
                    and len(fleet_agent_set) >= self.min_agents_for_fleet_alert):
                alerts.append({
                    "type": "fleet_cost_explosion",
                    "fleet_total_usd": round(fleet_total, 4),
                    "fleet_limit_usd": self.fleet_per_minute_limit,
                    "active_agents": len(fleet_agent_set),
                })

            if alerts:
                self._detect_count += 1
                return {
                    "detector": "cost_explosion",
                    "agent_id": agent_id,
                    "alerts": alerts,
                    "severity": (
                        "critical"
                        if agent_total > self.per_agent_per_minute_limit * self.explosion_ratio
                        else "high"
                    ),
                    "detected_at": ts,
                }
            return None
        except Exception:
            logger.exception("CostExplosionDetector.detect failed for agent_id=%s", agent_id)
            return None
        finally:
            self._detect_total_ms += (time.monotonic() - t0) * 1000

    def get_stats(self) -> dict:
        """获取检测器统计"""
        with self._lock:
            tracked = len(self._fleet_costs)
        return {
            "detector": "cost_explosion",
            "detection_count": self._detect_count,
            "tracked_agents": tracked,
            "avg_detect_ms": _avg_ms(
                self._detect_total_ms, self._detect_count
            ),
        }


@dataclass
class AgentCollusionDetector:
    """Agent串谋检测器 - 检测多个Agent之间的可疑协调行为"""
    # (agent_a, agent_b) sorted pair -> deque of (event_type, timestamp)
    _interaction_history: dict[tuple[str, str], deque] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=500))
    )
    # agent_id -> deque of (target_agent, action, timestamp)
    _agent_outbound: dict[str, deque] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=200))
    )
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _detect_count: int = field(default=0, init=False, repr=False)
    _detect_total_ms: float = field(default=0.0, init=False, repr=False)
    # Thresholds
    max_interactions_per_window: int = 20  # Interactions between same pair
    max_shared_resource_rate: int = 10  # Shared resource accesses per window
    coordination_window_seconds: int = 120  # 2 minutes
    min_colluding_agents: int = 2

    def detect(self, agent_id: str, target_agent_id: str,
               action: str = "message",
               shared_resource_id: str | None = None,
               timestamp: float | None = None) -> dict | None:
        """检测Agent串谋"""
        if not agent_id or not target_agent_id:
            return None
        if agent_id == target_agent_id:
            return None

        t0 = time.monotonic()
        try:
            ts = timestamp if timestamp is not None and timestamp > 0 else time.time()
            pair = tuple(sorted([agent_id, target_agent_id]))

            with self._lock:
                # Track pairwise interaction
                self._interaction_history[pair].append((action, ts))
                self._agent_outbound[agent_id].append((target_agent_id, action, ts))

                cutoff = ts - self.coordination_window_seconds

                # Count recent interactions between this pair
                pair_recent = sum(1 for _, t in self._interaction_history[pair] if t >= cutoff)

                # Count agents that agent_id is coordinating with
                outbound_recent = [
                    (tgt, act) for tgt, act, t in self._agent_outbound[agent_id] if t >= cutoff
                ]
                unique_targets = set(tgt for tgt, _ in outbound_recent)

            alerts = []

            # High-frequency bilateral communication
            if pair_recent > self.max_interactions_per_window:
                alerts.append({
                    "type": "excessive_bilateral_communication",
                    "agent_pair": sorted(pair),
                    "interaction_count": pair_recent,
                    "threshold": self.max_interactions_per_window,
                })

            # Fan-out coordination: one agent messaging many others
            if len(unique_targets) >= self.min_colluding_agents + 1:
                alerts.append({
                    "type": "fan_out_coordination",
                    "source_agent": agent_id,
                    "target_agents": sorted(unique_targets),
                    "target_count": len(unique_targets),
                })

            # Shared resource access pattern
            if shared_resource_id:
                shared_count = sum(
                    1 for _, act, t in self._agent_outbound[agent_id]
                    if t >= cutoff and act == f"resource:{shared_resource_id}"
                )
                if shared_count >= self.max_shared_resource_rate:
                    alerts.append({
                        "type": "shared_resource_collusion",
                        "resource_id": shared_resource_id,
                        "access_count": shared_count,
                        "threshold": self.max_shared_resource_rate,
                    })

            if alerts:
                self._detect_count += 1
                return {
                    "detector": "agent_collusion",
                    "agent_id": agent_id,
                    "target_agent_id": target_agent_id,
                    "alerts": alerts,
                    "severity": "high" if len(alerts) >= 2 else "medium",
                    "detected_at": ts,
                }
            return None
        except Exception:
            logger.exception(
                "AgentCollusionDetector.detect failed for agent_id=%s, target=%s",
                agent_id, target_agent_id,
            )
            return None
        finally:
            self._detect_total_ms += (time.monotonic() - t0) * 1000

    def get_stats(self) -> dict:
        """获取检测器统计"""
        with self._lock:
            tracked_pairs = len(self._interaction_history)
            tracked_agents = len(self._agent_outbound)
        return {
            "detector": "agent_collusion",
            "detection_count": self._detect_count,
            "tracked_pairs": tracked_pairs,
            "tracked_agents": tracked_agents,
            "avg_detect_ms": _avg_ms(
                self._detect_total_ms, self._detect_count
            ),
        }


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
        self.prompt_injection = PromptInjectionDetector()
        self.data_exfiltration = DataExfiltrationDetector()
        self.hallucination = HallucinationDetector()
        self.cost_explosion = CostExplosionDetector()
        self.agent_collusion = AgentCollusionDetector()
        self._total_detect_count: int = 0
        self._total_detect_ms: float = 0.0

    def detect_all(self, event_data: dict[str, Any]) -> list[dict]:
        """对一个Agent事件运行所有检测器"""
        if not isinstance(event_data, dict):
            return []

        alerts: list[dict] = []
        t0 = time.monotonic()

        agent_id = event_data.get("agent_id", "unknown")
        event_type = event_data.get("event_type", "unknown")
        ts = event_data.get("timestamp")

        try:
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
            if isinstance(cost, (int, float)) and cost > 0:
                result = self.cost_spike.detect(agent_id, cost, timestamp=ts)
                if result:
                    alerts.append(result)

            # Token explosion detection
            prompt_tokens = event_data.get("prompt_tokens", 0)
            completion_tokens = event_data.get("completion_tokens", 0)
            if (
                isinstance(prompt_tokens, (int, float)) and prompt_tokens > 0
                or isinstance(completion_tokens, (int, float)) and completion_tokens > 0
            ):
                result = self.token_explosion.detect(
                    agent_id, int(prompt_tokens), int(completion_tokens),
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
            if isinstance(latency, (int, float)) and latency > 0:
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

            # Prompt injection detection
            input_text = event_data.get("input_text", "")
            if input_text:
                result = self.prompt_injection.detect(
                    agent_id, input_text, timestamp=ts,
                )
                if result:
                    alerts.append(result)

            # Data exfiltration detection
            output_text = event_data.get("output_text", "")
            if tool_name and output_text:
                result = self.data_exfiltration.detect(
                    agent_id, tool_name, output_text,
                    output_size_bytes=event_data.get("output_size_bytes", 0),
                    timestamp=ts,
                )
                if result:
                    alerts.append(result)

            # Hallucination detection
            if output_text:
                result = self.hallucination.detect(
                    agent_id, output_text,
                    confidence=event_data.get("confidence", 1.0),
                    citation_count=event_data.get("citation_count", 0),
                    source_count=event_data.get("source_count", 0),
                    timestamp=ts,
                )
                if result:
                    alerts.append(result)

            # Cost explosion detection (fleet-level)
            if isinstance(cost, (int, float)) and cost > 0:
                result = self.cost_explosion.detect(
                    agent_id, cost,
                    model=event_data.get("model", ""),
                    timestamp=ts,
                )
                if result:
                    alerts.append(result)

            # Agent collusion detection
            target_agent = event_data.get("target_agent_id", "")
            if target_agent:
                result = self.agent_collusion.detect(
                    agent_id, target_agent,
                    action=event_data.get("collusion_action", "message"),
                    shared_resource_id=event_data.get("shared_resource_id"),
                    timestamp=ts,
                )
                if result:
                    alerts.append(result)
        except Exception:
            logger.exception("detect_all failed for event_data=%s", event_data)

        self._total_detect_count += len(alerts)
        self._total_detect_ms += (time.monotonic() - t0) * 1000
        return alerts

    def get_stats(self) -> dict[str, Any]:
        """获取所有检测器的聚合统计"""
        return {
            "total_detections": self._total_detect_count,
            "total_detect_ms": round(self._total_detect_ms, 3),
            "detectors": {
                "loop": self.loop_detector.get_stats(),
                "cost_spike": self.cost_spike.get_stats(),
                "token_explosion": self.token_explosion.get_stats(),
                "tool_abuse": self.tool_abuse.get_stats(),
                "timeout_cascade": self.timeout_cascade.get_stats(),
                "capability_drift": self.capability_drift.get_stats(),
                "resource_contention": self.resource_contention.get_stats(),
                "prompt_injection": self.prompt_injection.get_stats(),
                "data_exfiltration": self.data_exfiltration.get_stats(),
                "hallucination": self.hallucination.get_stats(),
                "cost_explosion": self.cost_explosion.get_stats(),
                "agent_collusion": self.agent_collusion.get_stats(),
            },
        }
