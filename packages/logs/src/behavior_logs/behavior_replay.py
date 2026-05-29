"""
AI Agent行为回放引擎
"""
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ReplayEvent(BaseModel):
    """回放事件"""
    sequence: int
    timestamp: datetime
    event_type: str
    agent_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    success: bool = True
    anomaly_score: float = 0.0


class ReplayState(BaseModel):
    """回放状态"""
    current_index: int = 0
    current_time: datetime | None = None
    is_playing: bool = False
    speed: float = 1.0  # 0.5x, 1x, 2x, 4x, 8x
    total_events: int = 0
    elapsed_ms: float = 0.0


class BehaviorReplay:
    """行为回放器"""

    def __init__(self):
        self._replays: dict[str, list[ReplayEvent]] = {}
        self._states: dict[str, ReplayState] = {}

    def load_trace(self, trace_id: str, events: list[dict[str, Any]]) -> None:
        """加载trace事件用于回放"""
        replay_events = []

        for i, event in enumerate(sorted(events, key=lambda e: e.get("timestamp", ""))):
            replay_events.append(ReplayEvent(
                sequence=i,
                timestamp=event.get("timestamp", _utc_now()),
                event_type=event.get("event_type", "unknown"),
                agent_id=event.get("agent_id", "unknown"),
                details={
                    "tool_name": event.get("tool_name"),
                    "model_name": event.get("model_name"),
                    "token_usage": event.get("token_usage"),
                    "properties": event.get("properties", {}),
                    "trace_id": event.get("trace_id"),
                    "session_id": event.get("session_id"),
                },
                duration_ms=event.get("latency_ms", 0),
                success=event.get("success", True),
                anomaly_score=event.get("anomaly_score", 0),
            ))

        self._replays[trace_id] = replay_events
        self._states[trace_id] = ReplayState(
            total_events=len(replay_events),
            current_time=replay_events[0].timestamp if replay_events else None,
        )

    def get_state(self, trace_id: str) -> ReplayState | None:
        """获取回放状态"""
        return self._states.get(trace_id)

    def get_current_event(self, trace_id: str) -> ReplayEvent | None:
        """获取当前回放事件"""
        state = self._states.get(trace_id)
        events = self._replays.get(trace_id, [])

        if not state or not events:
            return None

        if 0 <= state.current_index < len(events):
            return events[state.current_index]
        return None

    def step_forward(self, trace_id: str) -> ReplayEvent | None:
        """前进一步"""
        state = self._states.get(trace_id)
        events = self._replays.get(trace_id, [])

        if not state or not events:
            return None

        if state.current_index < len(events) - 1:
            state.current_index += 1
            state.current_time = events[state.current_index].timestamp
            state.elapsed_ms = sum(e.duration_ms for e in events[:state.current_index + 1])
            return events[state.current_index]
        return None

    def step_backward(self, trace_id: str) -> ReplayEvent | None:
        """后退一步"""
        state = self._states.get(trace_id)
        events = self._replays.get(trace_id, [])

        if not state or not events:
            return None

        if state.current_index > 0:
            state.current_index -= 1
            state.current_time = events[state.current_index].timestamp
            state.elapsed_ms = sum(e.duration_ms for e in events[:state.current_index + 1])
            return events[state.current_index]
        return None

    def jump_to(self, trace_id: str, index: int) -> ReplayEvent | None:
        """跳转到指定位置"""
        state = self._states.get(trace_id)
        events = self._replays.get(trace_id, [])

        if not state or not events:
            return None

        if 0 <= index < len(events):
            state.current_index = index
            state.current_time = events[index].timestamp
            state.elapsed_ms = sum(e.duration_ms for e in events[:index + 1])
            return events[index]
        return None

    def jump_to_anomaly(self, trace_id: str) -> ReplayEvent | None:
        """跳转到下一个异常事件"""
        state = self._states.get(trace_id)
        events = self._replays.get(trace_id, [])

        if not state or not events:
            return None

        # Find next anomaly after current position
        for i in range(state.current_index + 1, len(events)):
            if events[i].anomaly_score > 0.5 or not events[i].success:
                return self.jump_to(trace_id, i)

        return None

    def get_events_range(self, trace_id: str, start: int = 0,
                        limit: int = 50) -> list[ReplayEvent]:
        """获取事件范围"""
        events = self._replays.get(trace_id, [])
        return events[start:start + limit]

    def get_anomaly_events(self, trace_id: str) -> list[ReplayEvent]:
        """获取所有异常事件"""
        events = self._replays.get(trace_id, [])
        return [e for e in events if e.anomaly_score > 0.3 or not e.success]

    def get_timeline_summary(self, trace_id: str) -> dict[str, Any]:
        """获取时间线摘要"""
        events = self._replays.get(trace_id, [])
        state = self._states.get(trace_id)

        if not events:
            return {"trace_id": trace_id, "total_events": 0}

        anomaly_count = sum(1 for e in events if e.anomaly_score > 0.3)
        error_count = sum(1 for e in events if not e.success)
        total_duration = sum(e.duration_ms for e in events)

        return {
            "trace_id": trace_id,
            "total_events": len(events),
            "total_duration_ms": total_duration,
            "anomaly_count": anomaly_count,
            "error_count": error_count,
            "current_position": state.current_index if state else 0,
            "start_time": events[0].timestamp.isoformat() if events else None,
            "end_time": events[-1].timestamp.isoformat() if events else None,
        }
