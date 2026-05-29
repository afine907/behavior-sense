"""
LangChain回调处理器 - 自动追踪LangChain执行
"""
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from behavior_core.models.agent_event import AgentBehavior, AgentEventType, AgentType
from behavior_core.models.token_usage import TokenUsage
from behavior_core.models.tool_call import ToolCall, ToolType


def _utc_now() -> datetime:
    return datetime.now(UTC)


class BehaviorSenseCallbackHandler(BaseCallbackHandler):
    """BehaviorSense LangChain回调处理器"""

    def __init__(
        self,
        agent_id: str = "langchain-agent",
        agent_type: str = AgentType.LLM_AGENT,
        model_name: str | None = None,
        on_event: Any | None = None,
    ):
        super().__init__()
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.model_name = model_name
        self.on_event = on_event
        self._trace_id = str(uuid.uuid4())
        self._session_id = str(uuid.uuid4())
        self._current_span: dict[str, Any] = {}
        self._events: list[AgentBehavior] = []

    def _create_event(
        self,
        event_type: AgentEventType,
        **kwargs,
    ) -> AgentBehavior:
        """创建Agent事件"""
        event = AgentBehavior(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            event_type=event_type,
            trace_id=self._trace_id,
            session_id=self._session_id,
            model_name=self.model_name,
            **kwargs,
        )
        self._events.append(event)

        if self.on_event:
            self.on_event(event)

        return event

    @property
    def events(self) -> list[AgentBehavior]:
        """获取所有事件"""
        return list(self._events)

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        **kwargs: Any,
    ) -> None:
        """LLM开始"""
        self._current_span["start_time"] = time.time()
        self._current_span["prompts"] = prompts

        self._create_event(
            event_type=AgentEventType.LLM_REQUEST,
            properties={
                "model": serialized.get("name", "unknown"),
                "prompts": prompts,
            },
        )

    def on_llm_end(
        self,
        response: LLMResult,
        **kwargs: Any,
    ) -> None:
        """LLM结束"""
        latency_ms = 0
        if "start_time" in self._current_span:
            latency_ms = (time.time() - self._current_span["start_time"]) * 1000

        # Extract token usage
        token_usage = None
        if response.llm_output:
            usage = response.llm_output.get("token_usage", {})
            if usage:
                token_usage = TokenUsage(
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                    model_name=self.model_name,
                )

        self._create_event(
            event_type=AgentEventType.LLM_RESPONSE,
            latency_ms=latency_ms,
            token_usage=token_usage,
            properties={
                "generations": [[g.text for g in gens] for gens in response.generations],
            },
        )

        self._current_span.clear()

    def on_llm_error(
        self,
        error: BaseException,
        **kwargs: Any,
    ) -> None:
        """LLM错误"""
        latency_ms = 0
        if "start_time" in self._current_span:
            latency_ms = (time.time() - self._current_span["start_time"]) * 1000

        self._create_event(
            event_type=AgentEventType.ERROR,
            latency_ms=latency_ms,
            success=False,
            error_type=type(error).__name__,
            error_message=str(error),
        )

        self._current_span.clear()

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """工具开始"""
        self._current_span["start_time"] = time.time()
        self._current_span["tool_name"] = serialized.get("name", "unknown")

        self._create_event(
            event_type=AgentEventType.TOOL_CALL,
            tool_call=ToolCall(
                tool_name=serialized.get("name", "unknown"),
                tool_type=ToolType.CUSTOM,
                input_summary=input_str[:200],
            ),
        )

    def on_tool_end(
        self,
        output: str,
        **kwargs: Any,
    ) -> None:
        """工具结束"""
        latency_ms = 0
        if "start_time" in self._current_span:
            latency_ms = (time.time() - self._current_span["start_time"]) * 1000

        self._create_event(
            event_type=AgentEventType.TOOL_RESULT,
            latency_ms=latency_ms,
            tool_call=ToolCall(
                tool_name=self._current_span.get("tool_name", "unknown"),
                tool_type=ToolType.CUSTOM,
                output_summary=output[:200],
                latency_ms=latency_ms,
            ),
        )

        self._current_span.clear()

    def on_tool_error(
        self,
        error: BaseException,
        **kwargs: Any,
    ) -> None:
        """工具错误"""
        latency_ms = 0
        if "start_time" in self._current_span:
            latency_ms = (time.time() - self._current_span["start_time"]) * 1000

        self._create_event(
            event_type=AgentEventType.ERROR,
            latency_ms=latency_ms,
            success=False,
            error_type=type(error).__name__,
            error_message=str(error),
            tool_call=ToolCall(
                tool_name=self._current_span.get("tool_name", "unknown"),
                tool_type=ToolType.CUSTOM,
                success=False,
                error_type=type(error).__name__,
                error_message=str(error),
            ),
        )

        self._current_span.clear()

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Chain开始"""
        self._current_span["start_time"] = time.time()

        self._create_event(
            event_type=AgentEventType.PLAN_CREATE,
            properties={
                "chain": serialized.get("name", "unknown"),
                "inputs": {k: str(v)[:100] for k, v in inputs.items()},
            },
        )

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Chain结束"""
        latency_ms = 0
        if "start_time" in self._current_span:
            latency_ms = (time.time() - self._current_span["start_time"]) * 1000

        self._create_event(
            event_type=AgentEventType.PLAN_UPDATE,
            latency_ms=latency_ms,
            properties={
                "outputs": {k: str(v)[:100] for k, v in outputs.items()},
            },
        )

        self._current_span.clear()
