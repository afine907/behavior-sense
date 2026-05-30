# BehaviorSense Examples

## Basic Usage

See [basic_usage.py](basic_usage.py) for a simple example of:
- Creating a client
- Sending agent events
- Managing agent profiles
- Setting tags
- Querying statistics

## Monitoring

See [monitoring_example.py](monitoring_example.py) for:
- Monitoring all agents
- Checking anomaly scores
- Generating reports

## Running Examples

```bash
# Install dependencies
uv sync

# Run basic example
uv run python examples/basic_usage.py

# Run monitoring example
uv run python examples/monitoring_example.py
```

## SDK Reference

### Client

```python
from behavior_sdk import BehaviorSenseClient

async with BehaviorSenseClient(base_url="http://localhost:8001") as client:
    # Use client methods
    ...
```

### Models

```python
from behavior_sdk import AgentEvent, AgentProfile, TokenUsage

event = AgentEvent(
    agent_id="my-agent",
    event_type="tool_call",
    tool_call={"tool_name": "search", "latency_ms": 100},
)
```
