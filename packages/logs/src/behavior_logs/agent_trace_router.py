"""
Agent Trace Query API - backed by ClickHouse via AgentTraceRepository
"""
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from behavior_logs.repositories.agent_trace_repo import AgentTraceRepository

router = APIRouter(prefix="/api/traces", tags=["agent-traces"])


# ============================================================
# Response Models
# ============================================================


class SpanResponse(BaseModel):
    span_id: str
    trace_id: str
    parent_span_id: str | None = None
    name: str
    kind: str = "agent"
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float | None = None
    agent_id: str | None = None
    status: str = "ok"
    attributes: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list)


class TraceResponse(BaseModel):
    trace_id: str
    agent_id: str
    session_id: str | None = None
    task_id: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float | None = None
    span_count: int = 0
    error_count: int = 0
    has_timeout: bool = False
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    spans: list[SpanResponse] = Field(default_factory=list)


class TraceListResponse(BaseModel):
    traces: list[TraceResponse]
    total: int
    page: int
    page_size: int


class TraceTimelineEvent(BaseModel):
    time: datetime
    event_type: str
    span_id: str
    span_name: str
    agent_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class TraceWaterfall(BaseModel):
    """Waterfall visualization data."""

    trace_id: str
    total_duration_ms: float
    spans: list[dict[str, Any]]
    critical_path: list[str]


# ============================================================
# Dependency: ClickHouse repository
# ============================================================


async def get_trace_repo():
    """Yield an AgentTraceRepository and close it after the request."""
    from behavior_logs.main import settings

    password = settings.clickhouse_password.get_secret_value()
    auth = f"{settings.clickhouse_user}:{password}@" if password else ""
    clickhouse_url = (
        f"http://{auth}{settings.clickhouse_host}:8123/"
        f"{settings.clickhouse_database}"
    )
    repo = AgentTraceRepository(clickhouse_url=clickhouse_url)
    try:
        yield repo
    finally:
        await repo.close()


# ============================================================
# Helpers: map ClickHouse event rows -> span-like dicts
# ============================================================


def _event_to_span(event: dict[str, Any]) -> dict[str, Any]:
    """Convert an agent_event_logs row into a span-like dict."""
    start_time = event.get("timestamp")
    latency_ms = event.get("latency_ms") or 0
    end_time = None
    if start_time and latency_ms:
        end_time = start_time + timedelta(milliseconds=latency_ms)

    success = event.get("success")
    error_type = event.get("error_type")
    if success is False or error_type:
        status = "error"
    else:
        status = "ok"

    return {
        "span_id": event.get("event_id", ""),
        "trace_id": event.get("trace_id", ""),
        "parent_span_id": None,
        "name": event.get("tool_name") or event.get("event_type", "event"),
        "kind": "agent",
        "start_time": start_time,
        "end_time": end_time,
        "duration_ms": latency_ms if latency_ms else None,
        "agent_id": event.get("agent_id"),
        "status": status,
        "attributes": {
            "event_type": event.get("event_type"),
            "agent_type": event.get("agent_type"),
            "model_name": event.get("model_name"),
            "tool_name": event.get("tool_name"),
            "prompt_tokens": event.get("prompt_tokens", 0),
            "completion_tokens": event.get("completion_tokens", 0),
            "total_tokens": event.get("total_tokens", 0),
            "cost_usd": event.get("cost_usd", 0),
            "error_type": event.get("error_type"),
            "error_message": event.get("error_message"),
        },
        "events": [],
    }


def _trace_to_response(trace: dict[str, Any]) -> TraceResponse:
    """Map a ClickHouse agent_sessions row to a TraceResponse."""
    return TraceResponse(
        trace_id=trace.get("trace_id", trace.get("session_id", "")),
        agent_id=trace.get("agent_id", ""),
        session_id=trace.get("session_id"),
        task_id=trace.get("task_id"),
        start_time=trace.get("start_time"),
        end_time=trace.get("end_time"),
        duration_ms=trace.get("duration_ms"),
        span_count=trace.get("total_events", 0),
        error_count=trace.get("error_count", 0),
        has_timeout=bool(trace.get("timeout_count", 0)),
        total_tokens=trace.get("total_tokens", 0),
        total_cost_usd=trace.get("total_cost_usd", 0),
    )


def _calculate_span_depth(span: dict, all_spans: list[dict]) -> int:
    """Calculate nesting depth of a span."""
    depth = 0
    current_parent = span.get("parent_span_id")
    span_map = {s.get("span_id"): s for s in all_spans}

    while current_parent and depth < 20:
        parent = span_map.get(current_parent)
        if not parent:
            break
        depth += 1
        current_parent = parent.get("parent_span_id")

    return depth


def _find_critical_path(spans: list[dict]) -> list[str]:
    """Find the critical path (longest duration chain) through the trace."""
    if not spans:
        return []

    span_map = {s.get("span_id"): s for s in spans}
    children_map: dict[str, list[str]] = {}
    root_ids: list[str] = []

    for span in spans:
        span_id = span.get("span_id")
        parent_id = span.get("parent_span_id")

        if parent_id and parent_id in span_map:
            children_map.setdefault(parent_id, []).append(span_id)
        else:
            root_ids.append(span_id)

    def longest_path(span_id: str) -> list[str]:
        children = children_map.get(span_id, [])
        if not children:
            return [span_id]

        best_child_path: list[str] = []
        for child_id in children:
            child_path = longest_path(child_id)
            child_duration = sum(
                (span_map.get(sid, {}).get("duration_ms") or 0)
                for sid in child_path
            )
            best_duration = sum(
                (span_map.get(sid, {}).get("duration_ms") or 0)
                for sid in best_child_path
            )
            if child_duration > best_duration:
                best_child_path = child_path

        return [span_id] + best_child_path

    best_path: list[str] = []
    for root_id in root_ids:
        path = longest_path(root_id)
        path_duration = sum(
            (span_map.get(sid, {}).get("duration_ms") or 0) for sid in path
        )
        best_duration = sum(
            (span_map.get(sid, {}).get("duration_ms") or 0) for sid in best_path
        )
        if path_duration > best_duration:
            best_path = path

    return best_path


# ============================================================
# Trace Query Endpoints
# ============================================================


@router.get("", response_model=TraceListResponse)
async def list_traces(
    agent_id: str | None = Query(None),
    session_id: str | None = Query(None),
    task_id: str | None = Query(None),
    status: str | None = Query(None),
    has_error: bool | None = Query(None),
    min_duration_ms: float | None = Query(None),
    max_duration_ms: float | None = Query(None),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repo: AgentTraceRepository = Depends(get_trace_repo),
):
    """List traces with filtering."""
    traces, total = await repo.list_traces(
        agent_id=agent_id,
        session_id=session_id,
        task_id=task_id,
        has_error=has_error,
        min_duration_ms=min_duration_ms,
        max_duration_ms=max_duration_ms,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )

    return TraceListResponse(
        traces=[_trace_to_response(t) for t in traces],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats/overview")
async def get_trace_stats(
    repo: AgentTraceRepository = Depends(get_trace_repo),
):
    """Get trace statistics overview."""
    return await repo.get_stats()


@router.get("/{trace_id}", response_model=TraceResponse)
async def get_trace(
    trace_id: str,
    repo: AgentTraceRepository = Depends(get_trace_repo),
):
    """Get full trace with all spans."""
    trace = await repo.get_trace_with_events(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    response = _trace_to_response(trace)
    response.spans = [
        SpanResponse(**_event_to_span(evt)) for evt in trace.get("events", [])
    ]
    response.span_count = len(response.spans)
    return response


@router.get("/{trace_id}/spans")
async def get_trace_spans(
    trace_id: str,
    repo: AgentTraceRepository = Depends(get_trace_repo),
):
    """Get spans for a trace."""
    trace = await repo.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    events = await repo.get_trace_events(trace_id)
    spans = [_event_to_span(evt) for evt in events]
    return {"trace_id": trace_id, "spans": spans}


@router.get("/{trace_id}/waterfall", response_model=TraceWaterfall)
async def get_trace_waterfall(
    trace_id: str,
    repo: AgentTraceRepository = Depends(get_trace_repo),
):
    """Get waterfall visualization data for a trace."""
    trace = await repo.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    events = await repo.get_trace_events(trace_id)
    spans = [_event_to_span(evt) for evt in events]
    total_duration = trace.get("duration_ms") or 0

    # Build waterfall structure
    waterfall_spans: list[dict[str, Any]] = []
    for span in spans:
        span_start = span.get("start_time")
        span_duration = span.get("duration_ms") or 0

        # Calculate offset from trace start
        trace_start = trace.get("start_time")
        offset_ms = 0.0
        if span_start and trace_start:
            try:
                offset_ms = (span_start - trace_start).total_seconds() * 1000
            except (TypeError, AttributeError):
                offset_ms = 0.0

        waterfall_spans.append(
            {
                "span_id": span.get("span_id"),
                "name": span.get("name"),
                "kind": span.get("kind", "agent"),
                "depth": _calculate_span_depth(span, spans),
                "offset_ms": offset_ms,
                "duration_ms": span_duration,
                "status": span.get("status", "ok"),
                "agent_id": span.get("agent_id"),
            }
        )

    critical_path = _find_critical_path(spans)

    return TraceWaterfall(
        trace_id=trace_id,
        total_duration_ms=total_duration,
        spans=waterfall_spans,
        critical_path=critical_path,
    )


@router.get("/{trace_id}/timeline")
async def get_trace_timeline(
    trace_id: str,
    repo: AgentTraceRepository = Depends(get_trace_repo),
):
    """Get timeline events for a trace."""
    trace = await repo.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    events_data = await repo.get_trace_events(trace_id)
    spans = [_event_to_span(evt) for evt in events_data]
    timeline_events: list[dict[str, Any]] = []

    for span in spans:
        # Span start event
        timeline_events.append(
            {
                "time": span.get("start_time"),
                "event_type": "span_start",
                "span_id": span.get("span_id"),
                "span_name": span.get("name"),
                "agent_id": span.get("agent_id"),
                "kind": span.get("kind"),
            }
        )

        # Span end event
        if span.get("end_time"):
            timeline_events.append(
                {
                    "time": span.get("end_time"),
                    "event_type": "span_end",
                    "span_id": span.get("span_id"),
                    "span_name": span.get("name"),
                    "agent_id": span.get("agent_id"),
                    "status": span.get("status"),
                    "duration_ms": span.get("duration_ms"),
                }
            )

        # Nested span events (from the attributes / events list)
        for event in span.get("events", []):
            timeline_events.append(
                {
                    "time": event.get("timestamp", span.get("start_time")),
                    "event_type": event.get("name", "event"),
                    "span_id": span.get("span_id"),
                    "span_name": span.get("name"),
                    "agent_id": span.get("agent_id"),
                    "details": event.get("attributes", {}),
                }
            )

    # Sort by time
    timeline_events.sort(key=lambda e: str(e.get("time", "")))

    return {"trace_id": trace_id, "events": timeline_events}


@router.get("/{trace_id}/errors")
async def get_trace_errors(
    trace_id: str,
    repo: AgentTraceRepository = Depends(get_trace_repo),
):
    """Get error details from a trace."""
    trace = await repo.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    events_data = await repo.get_trace_events(trace_id)
    spans = [_event_to_span(evt) for evt in events_data]
    errors: list[dict[str, Any]] = []

    for span in spans:
        if span.get("status") in ("error", "timeout"):
            errors.append(
                {
                    "span_id": span.get("span_id"),
                    "span_name": span.get("name"),
                    "agent_id": span.get("agent_id"),
                    "status": span.get("status"),
                    "status_message": span.get("attributes", {}).get(
                        "error_message"
                    ),
                    "start_time": span.get("start_time"),
                    "duration_ms": span.get("duration_ms"),
                }
            )

    return {"trace_id": trace_id, "errors": errors, "error_count": len(errors)}
