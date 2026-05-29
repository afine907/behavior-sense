"""
Agent执行追踪查询API
"""
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

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
    """Waterfall visualization data"""
    trace_id: str
    total_duration_ms: float
    spans: list[dict[str, Any]]  # Nested span structure for waterfall
    critical_path: list[str]  # span IDs on critical path


# ============================================================
# In-memory trace store (production would use ClickHouse)
# ============================================================
_traces: dict[str, dict] = {}


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
):
    """List traces with filtering"""
    traces = list(_traces.values())

    if agent_id:
        traces = [t for t in traces if t.get("agent_id") == agent_id]
    if session_id:
        traces = [t for t in traces if t.get("session_id") == session_id]
    if task_id:
        traces = [t for t in traces if t.get("task_id") == task_id]
    if has_error is not None:
        traces = [t for t in traces if (t.get("error_count", 0) > 0) == has_error]
    if min_duration_ms is not None:
        traces = [t for t in traces if (t.get("duration_ms") or 0) >= min_duration_ms]
    if max_duration_ms is not None:
        traces = [t for t in traces if (t.get("duration_ms") or 0) <= max_duration_ms]

    # Sort by start_time descending
    traces.sort(key=lambda t: t.get("start_time", ""), reverse=True)

    total = len(traces)
    start = (page - 1) * page_size
    end = start + page_size
    page_traces = traces[start:end]

    return TraceListResponse(
        traces=[TraceResponse(**t) for t in page_traces],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats/overview")
async def get_trace_stats():
    """Get trace statistics overview"""
    total_traces = len(_traces)
    total_spans = sum(len(t.get("spans", [])) for t in _traces.values())
    error_traces = sum(1 for t in _traces.values() if t.get("error_count", 0) > 0)

    durations = [t.get("duration_ms", 0) or 0 for t in _traces.values() if t.get("duration_ms")]
    avg_duration = sum(durations) / len(durations) if durations else 0

    return {
        "total_traces": total_traces,
        "total_spans": total_spans,
        "error_traces": error_traces,
        "error_rate": error_traces / total_traces if total_traces > 0 else 0,
        "avg_duration_ms": round(avg_duration, 2),
    }


@router.get("/{trace_id}", response_model=TraceResponse)
async def get_trace(trace_id: str):
    """Get full trace with all spans"""
    if trace_id not in _traces:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    return TraceResponse(**_traces[trace_id])


@router.get("/{trace_id}/spans")
async def get_trace_spans(trace_id: str):
    """Get spans for a trace"""
    if trace_id not in _traces:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    return {"trace_id": trace_id, "spans": _traces[trace_id].get("spans", [])}


@router.get("/{trace_id}/waterfall", response_model=TraceWaterfall)
async def get_trace_waterfall(trace_id: str):
    """Get waterfall visualization data for a trace"""
    if trace_id not in _traces:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    trace = _traces[trace_id]
    spans = trace.get("spans", [])
    total_duration = trace.get("duration_ms", 0) or 0

    # Build waterfall structure
    waterfall_spans = []
    for span in spans:
        span_start = span.get("start_time")
        span_duration = span.get("duration_ms", 0) or 0

        # Calculate offset from trace start
        if span_start and trace.get("start_time"):
            try:
                start_dt = datetime.fromisoformat(str(span_start))
                trace_start_dt = datetime.fromisoformat(str(trace["start_time"]))
                offset_ms = (start_dt - trace_start_dt).total_seconds() * 1000
            except (ValueError, TypeError):
                offset_ms = 0
        else:
            offset_ms = 0

        waterfall_spans.append({
            "span_id": span.get("span_id"),
            "name": span.get("name"),
            "kind": span.get("kind", "agent"),
            "depth": _calculate_span_depth(span, spans),
            "offset_ms": offset_ms,
            "duration_ms": span_duration,
            "status": span.get("status", "ok"),
            "agent_id": span.get("agent_id"),
        })

    # Calculate critical path (longest chain)
    critical_path = _find_critical_path(spans)

    return TraceWaterfall(
        trace_id=trace_id,
        total_duration_ms=total_duration,
        spans=waterfall_spans,
        critical_path=critical_path,
    )


@router.get("/{trace_id}/timeline")
async def get_trace_timeline(trace_id: str):
    """Get timeline events for a trace"""
    if trace_id not in _traces:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    trace = _traces[trace_id]
    events = []

    for span in trace.get("spans", []):
        # Add span start event
        events.append({
            "time": span.get("start_time"),
            "event_type": "span_start",
            "span_id": span.get("span_id"),
            "span_name": span.get("name"),
            "agent_id": span.get("agent_id"),
            "kind": span.get("kind"),
        })

        # Add span end event if available
        if span.get("end_time"):
            events.append({
                "time": span.get("end_time"),
                "event_type": "span_end",
                "span_id": span.get("span_id"),
                "span_name": span.get("name"),
                "agent_id": span.get("agent_id"),
                "status": span.get("status"),
                "duration_ms": span.get("duration_ms"),
            })

        # Add span events
        for event in span.get("events", []):
            events.append({
                "time": event.get("timestamp", span.get("start_time")),
                "event_type": event.get("name", "event"),
                "span_id": span.get("span_id"),
                "span_name": span.get("name"),
                "agent_id": span.get("agent_id"),
                "details": event.get("attributes", {}),
            })

    # Sort by time
    events.sort(key=lambda e: str(e.get("time", "")))

    return {"trace_id": trace_id, "events": events}


@router.get("/{trace_id}/errors")
async def get_trace_errors(trace_id: str):
    """Get error details from a trace"""
    if trace_id not in _traces:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    trace = _traces[trace_id]
    errors = []

    for span in trace.get("spans", []):
        if span.get("status") in ("error", "timeout"):
            errors.append({
                "span_id": span.get("span_id"),
                "span_name": span.get("name"),
                "agent_id": span.get("agent_id"),
                "status": span.get("status"),
                "status_message": span.get("attributes", {}).get("error_message"),
                "start_time": span.get("start_time"),
                "duration_ms": span.get("duration_ms"),
            })

    return {"trace_id": trace_id, "errors": errors, "error_count": len(errors)}


# ============================================================
# Helper functions
# ============================================================

def _calculate_span_depth(span: dict, all_spans: list[dict]) -> int:
    """Calculate nesting depth of a span"""
    depth = 0
    current_parent = span.get("parent_span_id")
    span_map = {s.get("span_id"): s for s in all_spans}

    while current_parent and depth < 20:  # prevent infinite loop
        parent = span_map.get(current_parent)
        if not parent:
            break
        depth += 1
        current_parent = parent.get("parent_span_id")

    return depth


def _find_critical_path(spans: list[dict]) -> list[str]:
    """Find the critical path (longest duration chain) through the trace"""
    if not spans:
        return []

    span_map = {s.get("span_id"): s for s in spans}
    children_map: dict[str, list[str]] = {}
    root_ids = []

    for span in spans:
        span_id = span.get("span_id")
        parent_id = span.get("parent_span_id")

        if parent_id and parent_id in span_map:
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(span_id)
        else:
            root_ids.append(span_id)

    # DFS to find longest path
    def longest_path(span_id: str) -> list[str]:
        children = children_map.get(span_id, [])
        if not children:
            return [span_id]

        best_child_path = []
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

    # Find best root
    best_path = []
    for root_id in root_ids:
        path = longest_path(root_id)
        path_duration = sum(
            (span_map.get(sid, {}).get("duration_ms") or 0)
            for sid in path
        )
        best_duration = sum(
            (span_map.get(sid, {}).get("duration_ms") or 0)
            for sid in best_path
        )
        if path_duration > best_duration:
            best_path = path

    return best_path
