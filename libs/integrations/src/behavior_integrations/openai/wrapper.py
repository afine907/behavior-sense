"""
OpenAI SDK包装器 - 自动追踪OpenAI调用
"""
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from openai import OpenAI, AsyncOpenAI

from behavior_core.models.agent_event import AgentBehavior, AgentEventType, AgentType
from behavior_core.models.token_usage import TokenUsage
from behavior_core.models.tool_call import ToolCall, ToolType


def _utc_now() -> datetime:
    return datetime.now(UTC)


class BehaviorSenseOpenAIWrapper:
    """BehaviorSense OpenAI包装器"""

    def __init__(
        self,
        client: OpenAI | AsyncOpenAI | None = None,
        agent_id: str = "openai-agent",
        on_event: Any | None = None,
    ):
        self.client = client or OpenAI()
        self.agent_id = agent_id
        self.on_event = on_event
        self._trace_id = str(uuid.uuid4())
        self._events: list[AgentBehavior] = []

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

    @property
    def events(self) -> list[AgentBehavior]:
        return list(self._events)

    def chat_completions_create(self, **kwargs) -> Any:
        """包装chat.completions.create"""
        start_time = time.time()

        self._create_event(
            event_type=AgentEventType.LLM_REQUEST,
            model_name=kwargs.get("model"),
            properties={"messages": kwargs.get("messages", [])},
        )

        try:
            response = self.client.chat.completions.create(**kwargs)
            latency_ms = (time.time() - start_time) * 1000

            # Extract token usage
            token_usage = None
            if response.usage:
                token_usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                    model_name=kwargs.get("model"),
                )

            self._create_event(
                event_type=AgentEventType.LLM_RESPONSE,
                latency_ms=latency_ms,
                token_usage=token_usage,
                model_name=kwargs.get("model"),
                properties={
                    "choices": [
                        {"role": c.message.role, "content": c.message.content}
                        for c in response.choices
                    ],
                },
            )

            return response

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._create_event(
                event_type=AgentEventType.ERROR,
                latency_ms=latency_ms,
                success=False,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise

    def embeddings_create(self, **kwargs) -> Any:
        """包装embeddings.create"""
        start_time = time.time()

        self._create_event(
            event_type=AgentEventType.LLM_REQUEST,
            model_name=kwargs.get("model"),
            properties={"input": kwargs.get("input", "")},
        )

        try:
            response = self.client.embeddings.create(**kwargs)
            latency_ms = (time.time() - start_time) * 1000

            self._create_event(
                event_type=AgentEventType.LLM_RESPONSE,
                latency_ms=latency_ms,
                model_name=kwargs.get("model"),
            )

            return response

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._create_event(
                event_type=AgentEventType.ERROR,
                latency_ms=latency_ms,
                success=False,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise
