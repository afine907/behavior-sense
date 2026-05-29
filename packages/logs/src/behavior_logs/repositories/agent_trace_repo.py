"""
Agent Trace Repository - ClickHouse implementation
"""

from datetime import UTC, datetime
from typing import Any

import httpx
import orjson
from behavior_core.utils.logging import get_logger

logger = get_logger(__name__)


class AgentTraceRepository:
    """ClickHouse repository for agent execution traces and spans."""

    def __init__(self, clickhouse_url: str = "http://localhost:8123"):
        self.clickhouse_url = clickhouse_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _execute(self, query: str, params: dict | None = None) -> list[dict]:
        """Execute a ClickHouse query via HTTP interface and return rows as dicts."""
        client = await self._get_client()
        response = await client.post(
            f"{self.clickhouse_url}/",
            data=query,
            params={"default_format": "JSONEachRow"},
        )
        response.raise_for_status()

        if not response.text.strip():
            return []

        lines = response.text.strip().split("\n")
        return [orjson.loads(line) for line in lines if line.strip()]

    # ------------------------------------------------------------------
    # Trace listing
    # ------------------------------------------------------------------

    async def list_traces(
        self,
        agent_id: str | None = None,
        session_id: str | None = None,
        task_id: str | None = None,
        has_error: bool | None = None,
        min_duration_ms: float | None = None,
        max_duration_ms: float | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return (trace_dicts, total) with filtering and pagination."""
        conditions: list[str] = []
        params: dict[str, str] = {}

        if agent_id:
            conditions.append("agent_id = {agent_id:String}")
            params["agent_id"] = agent_id
        if session_id:
            conditions.append("session_id = {session_id:String}")
            params["session_id"] = session_id
        if task_id:
            conditions.append("task_id = {task_id:String}")
            params["task_id"] = task_id
        if has_error is not None:
            if has_error:
                conditions.append("error_count > 0")
            else:
                conditions.append("error_count = 0")
        if min_duration_ms is not None:
            conditions.append("duration_ms >= {min_duration:Float64}")
            params["min_duration"] = str(min_duration_ms)
        if max_duration_ms is not None:
            conditions.append("duration_ms <= {max_duration:Float64}")
            params["max_duration"] = str(max_duration_ms)
        if start_time:
            conditions.append("start_time >= {start_time:DateTime64(3)}")
            params["start_time"] = start_time.isoformat()
        if end_time:
            conditions.append("start_time <= {end_time:DateTime64(3)}")
            params["end_time"] = end_time.isoformat()

        where = " AND ".join(conditions) if conditions else "1=1"
        offset = (page - 1) * page_size

        # Total count
        count_query = f"SELECT count() as total FROM agent_sessions WHERE {where}"
        count_result = await self._execute(count_query, params)
        total = count_result[0]["total"] if count_result else 0

        # Page of traces
        query = f"""
        SELECT
            session_id AS trace_id,
            agent_id,
            session_id,
            task_id,
            goal,
            status,
            start_time,
            end_time,
            duration_ms,
            total_events,
            total_tool_calls,
            total_llm_calls,
            total_tokens,
            total_cost_usd,
            error_count,
            timeout_count,
            anomaly_score
        FROM agent_sessions
        WHERE {where}
        ORDER BY start_time DESC
        LIMIT {page_size} OFFSET {offset}
        """
        traces = await self._execute(query, params)

        return traces, total

    # ------------------------------------------------------------------
    # Single trace
    # ------------------------------------------------------------------

    async def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        """Return the trace record or None."""
        query = """
        SELECT
            session_id AS trace_id,
            agent_id,
            session_id,
            task_id,
            goal,
            status,
            start_time,
            end_time,
            duration_ms,
            total_events,
            total_tool_calls,
            total_llm_calls,
            total_tokens,
            total_cost_usd,
            error_count,
            timeout_count,
            anomaly_score
        FROM agent_sessions
        WHERE session_id = {trace_id:String}
        """
        result = await self._execute(query, {"trace_id": trace_id})
        return result[0] if result else None

    async def get_trace_with_events(self, trace_id: str) -> dict[str, Any] | None:
        """Return the trace record with its events attached, or None."""
        trace = await self.get_trace(trace_id)
        if trace is None:
            return None

        events = await self.get_trace_events(trace_id)
        trace["events"] = events
        return trace

    # ------------------------------------------------------------------
    # Events (used as spans for waterfall / timeline)
    # ------------------------------------------------------------------

    async def get_trace_events(self, trace_id: str) -> list[dict[str, Any]]:
        """Return all events for a trace, ordered by timestamp."""
        query = """
        SELECT
            event_id,
            agent_id,
            agent_type,
            event_type,
            timestamp,
            trace_id,
            session_id,
            task_id,
            model_name,
            tool_name,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            cost_usd,
            latency_ms,
            success,
            error_type,
            error_message,
            properties
        FROM agent_event_logs
        WHERE trace_id = {trace_id:String}
        ORDER BY timestamp ASC
        """
        return await self._execute(query, {"trace_id": trace_id})

    # ------------------------------------------------------------------
    # Aggregations / stats
    # ------------------------------------------------------------------

    async def get_stats(self) -> dict[str, Any]:
        """Return aggregated trace statistics."""
        query = """
        SELECT
            count()                AS total_traces,
            sum(total_events)      AS total_events,
            sum(error_count)       AS error_traces,
            avg(duration_ms)       AS avg_duration_ms
        FROM agent_sessions
        """
        result = await self._execute(query)
        if not result:
            return {
                "total_traces": 0,
                "total_spans": 0,
                "error_traces": 0,
                "error_rate": 0,
                "avg_duration_ms": 0,
            }

        row = result[0]
        total_traces = row.get("total_traces", 0)
        error_traces = row.get("error_traces", 0)

        return {
            "total_traces": total_traces,
            "total_spans": row.get("total_events", 0),
            "error_traces": error_traces,
            "error_rate": error_traces / total_traces if total_traces > 0 else 0,
            "avg_duration_ms": round(row.get("avg_duration_ms", 0), 2),
        }

    # ------------------------------------------------------------------
    # Insert operations (kept for completeness)
    # ------------------------------------------------------------------

    async def insert_event(self, event: dict[str, Any]) -> None:
        """Insert a single agent event into ClickHouse."""
        query = """
        INSERT INTO agent_event_logs (
            event_id, agent_id, agent_type, event_type, timestamp,
            trace_id, session_id, task_id, model_name, tool_name,
            prompt_tokens, completion_tokens, total_tokens, cached_tokens,
            cost_usd, latency_ms, success, error_type, error_message,
            properties
        ) VALUES (
            {event_id:String}, {agent_id:String}, {agent_type:String},
            {event_type:String}, {timestamp:DateTime64(3)},
            {trace_id:String}, {session_id:String}, {task_id:String},
            {model_name:String}, {tool_name:String},
            {prompt_tokens:UInt32}, {completion_tokens:UInt32},
            {total_tokens:UInt32}, {cached_tokens:UInt32},
            {cost_usd:Float64}, {latency_ms:Float64},
            {success:UInt8}, {error_type:String}, {error_message:String},
            {properties:String}
        )
        """
        await self._execute(
            query,
            {
                "event_id": event.get("event_id", ""),
                "agent_id": event.get("agent_id", ""),
                "agent_type": event.get("agent_type", ""),
                "event_type": event.get("event_type", ""),
                "timestamp": event.get("timestamp", datetime.now(UTC)),
                "trace_id": event.get("trace_id", ""),
                "session_id": event.get("session_id", ""),
                "task_id": event.get("task_id", ""),
                "model_name": event.get("model_name", ""),
                "tool_name": event.get("tool_name", ""),
                "prompt_tokens": event.get("prompt_tokens", 0),
                "completion_tokens": event.get("completion_tokens", 0),
                "total_tokens": event.get("total_tokens", 0),
                "cached_tokens": event.get("cached_tokens", 0),
                "cost_usd": event.get("cost_usd", 0),
                "latency_ms": event.get("latency_ms", 0),
                "success": 1 if event.get("success", True) else 0,
                "error_type": event.get("error_type", ""),
                "error_message": event.get("error_message", ""),
                "properties": event.get("properties", "{}"),
            },
        )

    async def insert_session(self, session: dict[str, Any]) -> None:
        """Insert a session/trace summary into ClickHouse."""
        query = """
        INSERT INTO agent_sessions (
            session_id, agent_id, agent_type, task_id, goal, status,
            start_time, end_time, duration_ms,
            total_events, total_tool_calls, total_llm_calls,
            total_tokens, total_cost_usd,
            error_count, timeout_count, anomaly_score
        ) VALUES (
            {session_id:String}, {agent_id:String}, {agent_type:String},
            {task_id:String}, {goal:String}, {status:String},
            {start_time:DateTime64(3)}, {end_time:Nullable(DateTime64(3))},
            {duration_ms:Nullable(Float64)},
            {total_events:UInt32}, {total_tool_calls:UInt32},
            {total_llm_calls:UInt32}, {total_tokens:UInt64},
            {total_cost_usd:Float64},
            {error_count:UInt32}, {timeout_count:UInt32},
            {anomaly_score:Float32}
        )
        """
        await self._execute(query, session)
