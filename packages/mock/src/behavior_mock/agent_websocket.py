"""
Agent实时事件WebSocket端点
"""
import asyncio
import json
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter(tags=["agent-websocket"])


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


def _generate_realtime_event() -> dict[str, Any]:
    """Generate a single real-time agent event for streaming"""
    import random

    agents = [
        {"id": "agent-coder-002", "type": "llm_agent", "model": "gpt-4"},
        {"id": "agent-researcher-001", "type": "llm_agent", "model": "claude-3-opus"},
        {"id": "agent-assistant-005", "type": "llm_agent", "model": "claude-3-haiku"},
        {"id": "agent-analyst-003", "type": "workflow_agent", "model": "claude-3-sonnet"},
        {"id": "agent-orchestrator-004", "type": "multi_agent", "model": "gpt-4-turbo"},
    ]

    event_types = ["tool_call", "llm_request", "llm_response", "memory_read", "delegation", "error"]
    tools = ["code_execution", "web_search", "file_read", "database", "calculator", "terminal"]

    agent = random.choice(agents)
    event_type = random.choice(event_types)

    return {
        "event_id": str(uuid.uuid4()),
        "agent_id": agent["id"],
        "agent_type": agent["type"],
        "event_type": event_type,
        "timestamp": datetime.now(UTC).isoformat(),
        "model_name": agent["model"],
        "tool_name": random.choice(tools) if event_type == "tool_call" else None,
        "latency_ms": round(random.uniform(50, 3000), 1),
        "success": random.random() > 0.05,
        "token_usage": {
            "prompt_tokens": random.randint(500, 5000),
            "completion_tokens": random.randint(100, 2000),
            "cost_usd": round(random.uniform(0.001, 0.05), 4),
        } if event_type in ("llm_request", "llm_response") else None,
    }


@router.websocket("/ws/agent-events")
async def websocket_agent_events(websocket: WebSocket):
    """WebSocket endpoint for real-time agent event streaming"""
    await manager.connect(websocket)

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to agent event stream",
            "timestamp": datetime.now(UTC).isoformat(),
        })

        # Stream events
        while True:
            # Generate event
            event = _generate_realtime_event()

            # Send to client
            await websocket.send_json({
                "type": "agent_event",
                "data": event,
            })

            # Random delay between events (100ms - 2s)
            await asyncio.sleep(0.1 + (time.time() % 1.9))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time alert streaming"""
    await manager.connect(websocket)

    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to alert stream",
        })

        while True:
            # Generate occasional alerts
            await asyncio.sleep(5 + (time.time() % 10))

            alert_types = ["cost_spike", "dead_loop", "timeout_cascade", "capability_drift"]
            severities = ["low", "medium", "high", "critical"]

            await websocket.send_json({
                "type": "alert",
                "data": {
                    "alert_id": str(uuid.uuid4()),
                    "alert_type": alert_types[int(time.time()) % len(alert_types)],
                    "severity": severities[int(time.time()) % len(severities)],
                    "agent_id": f"agent-{['coder', 'researcher', 'assistant', 'analyst'][int(time.time()) % 4]}-00{int(time.time()) % 5 + 1}",
                    "message": "Real-time alert from WebSocket stream",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
