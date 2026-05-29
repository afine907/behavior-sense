"""
ClickHouse repositories for the logs service.
"""

from behavior_logs.repositories.agent_trace_repo import AgentTraceRepository
from behavior_logs.repositories.event_repo import EventLogRepository

__all__ = [
    "AgentTraceRepository",
    "EventLogRepository",
]
