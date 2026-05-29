"""
LlamaIndex回调处理器
"""
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from llama_index.core.callbacks import CallbackManager
from llama_index.core.callbacks.base import BaseCallbackHandler

from behavior_core.models.agent_event import AgentBehavior, AgentEventType, AgentType
from behavior_core.models.token_usage import TokenUsage


def _utc_now() -> datetime:
    return datetime.now(UTC)


class BehaviorSenseCallbackHandler(BaseCallbackHandler):
    """BehaviorSense LlamaIndex回调处理器"""

    def __init__(
        self,
        agent_id: str = "llamaindex-agent",
        on_event: Any | None = None,
    ):
        super().__init__()
        self.agent_id = agent_id
        self.on_event = on_event
        self._trace_id = str(uuid.uuid4())
        self._events: list[AgentBehavior] = []
        self._start_times: dict[str, float] = {}

    def _create_event(self, event_type: AgentEventType, **kwargs) -> AgentBehavior:
        event = AgentBehavior(
            agent_id=self.agent_id,
            agent_type=AgentType.LLM_AGENT,
            event_type=event_type,
            trace_id=self._trace_id,
            **kwargs,
        )
        self._events.append(event)
        if self.on_event:
            self.on_event(event)
        return event

    def on_event_start(self, event_type: str, payload: dict | None = None, **kwargs) -> str:
        event_id = str(uuid.uuid4())
        self._start_times[event_id] = time.time()

        if "llm" in event_type.lower():
            self._create_event(
                event_type=AgentEventType.LLM_REQUEST,
                properties={"event_type": event_type, "payload": payload},
            )
        elif "tool" in event_type.lower():
            self._create_event(
                event_type=AgentEventType.TOOL_CALL,
                properties={"event_type": event_type, "payload": payload},
            )

        return event_id

    def on_event_end(self, event_id: str, **kwargs) -> None:
        latency_ms = 0
        if event_id in self._start_times:
            latency_ms = (time.time() - self._start_times[event_id]) * 1000

        self._create_event(
            event_type=AgentEventType.TOOL_RESULT,
            latency_ms=latency_ms,
        )

    def start_trace(self, trace_id: str | None = None) -> None:
        self._trace_id = trace_id or str(uuid.uuid4())

    def end_trace(self, trace_id: str | None = None) -> None:
        pass

    @property
    def events(self) -> list[AgentBehavior]:
        return list(self._events)
