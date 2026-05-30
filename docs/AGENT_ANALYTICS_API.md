# BehaviorSense Agent Analytics - API Reference

## Agent Mock API (`/api/agent-mock`)

### Generate Events
```http
POST /api/agent-mock/generate
Content-Type: application/json

{
  "agent_id": "agent-001",
  "agent_type": "llm_agent",
  "model_name": "gpt-4",
  "count": 10,
  "include_tokens": true,
  "include_tools": true
}
```

### Start Scenario
```http
POST /api/agent-mock/scenario/start
Content-Type: application/json

{
  "scenario": "normal|loop|cost_explosion|cascading_failure",
  "agent_count": 3,
  "duration_events": 100,
  "params": {}
}
```

## Agent Insight API (`/api/agents`)

### List Agents
```http
GET /api/agents?agent_type=llm_agent&status=active&page=1&page_size=20
```

### Get Agent Profile
```http
GET /api/agents/{agent_id}
```

### Update Agent Profile
```http
PUT /api/agents/{agent_id}
Content-Type: application/json

{
  "agent_name": "My Agent",
  "agent_type": "llm_agent",
  "model_name": "gpt-4"
}
```

### Get Agent Tags
```http
GET /api/agents/{agent_id}/tags
```

### Update Agent Tag
```http
PUT /api/agents/{agent_id}/tags
Content-Type: application/json

{
  "tag_name": "risk_level",
  "tag_value": "high",
  "source": "RULE",
  "confidence": 0.95
}
```

### Get Agent Statistics
```http
GET /api/agents/{agent_id}/stats
GET /api/agents/{agent_id}/stats/cost
GET /api/agents/{agent_id}/stats/performance
```

### Compare Agents
```http
POST /api/agents/compare
Content-Type: application/json

{
  "agent_ids": ["agent-1", "agent-2"],
  "metrics": ["success_rate", "avg_latency", "total_cost"]
}
```

### Risk Assessment
```http
GET /api/agents/{agent_id}/risk
```

### Global Overview
```http
GET /api/agents/stats/overview
GET /api/agents/stats/cost
```

## Agent Trace API (`/api/traces`)

### List Traces
```http
GET /api/traces?agent_id=xxx&has_error=true&page=1&page_size=20
```

### Get Trace
```http
GET /api/traces/{trace_id}
```

### Get Waterfall
```http
GET /api/traces/{trace_id}/waterfall
```

### Get Timeline
```http
GET /api/traces/{trace_id}/timeline
```

### Get Errors
```http
GET /api/traces/{trace_id}/errors
```

## WebSocket APIs

### Real-time Agent Events
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/agent-events');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.type, data.data);
};
```

### Real-time Alerts
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/alerts');
ws.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  console.log(alert.severity, alert.message);
};
```
