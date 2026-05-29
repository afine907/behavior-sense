-- ClickHouse Schema for AI Agent Behavior Analytics
-- Run after the base init.sql

-- ============================================================
-- Agent Event Logs (high-throughput append-only)
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_event_logs (
    event_id String,
    event_date Date DEFAULT toDate(timestamp),
    agent_id LowCardinality(String),
    agent_type LowCardinality(String),
    event_type LowCardinality(String),
    timestamp DateTime64(3, 'UTC'),
    trace_id String DEFAULT '',
    session_id String DEFAULT '',
    task_id String DEFAULT '',
    model_name LowCardinality(String) DEFAULT '',
    tool_name LowCardinality(String) DEFAULT '',

    -- Token usage
    prompt_tokens UInt32 DEFAULT 0,
    completion_tokens UInt32 DEFAULT 0,
    total_tokens UInt32 DEFAULT 0,
    cached_tokens UInt32 DEFAULT 0,
    cost_usd Float64 DEFAULT 0.0,

    -- Performance
    latency_ms Float64 DEFAULT 0.0,
    success UInt8 DEFAULT 1,
    error_type LowCardinality(String) DEFAULT '',
    error_message String DEFAULT '',

    -- Context
    properties String DEFAULT '{}',
    tags Array(String) DEFAULT [],

    -- Ingestion
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (agent_id, event_date, timestamp)
TTL event_date + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;


-- ============================================================
-- Agent Token Usage (aggregated materialized view)
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_token_usage_mv (
    agent_id String,
    model_name String,
    event_date Date,
    hour DateTime,

    total_prompt_tokens UInt64,
    total_completion_tokens UInt64,
    total_tokens UInt64,
    total_cached_tokens UInt64,
    total_cost_usd Float64,
    request_count UInt64,
    avg_cost_per_request Float64
) ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (agent_id, model_name, event_date, hour);


CREATE MATERIALIZED VIEW IF NOT EXISTS agent_token_usage_mv_view
TO agent_token_usage_mv AS
SELECT
    agent_id,
    model_name,
    event_date,
    toStartOfHour(timestamp) AS hour,
    sum(prompt_tokens) AS total_prompt_tokens,
    sum(completion_tokens) AS total_completion_tokens,
    sum(total_tokens) AS total_tokens,
    sum(cached_tokens) AS total_cached_tokens,
    sum(cost_usd) AS total_cost_usd,
    count() AS request_count,
    avg(cost_usd) AS avg_cost_per_request
FROM agent_event_logs
WHERE event_type IN ('llm_request', 'llm_response')
GROUP BY agent_id, model_name, event_date, hour;


-- ============================================================
-- Agent Tool Usage (aggregated materialized view)
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_tool_usage_mv (
    agent_id String,
    tool_name String,
    tool_type String,
    event_date Date,
    hour DateTime,

    call_count UInt64,
    success_count UInt64,
    error_count UInt64,
    avg_latency_ms Float64,
    total_latency_ms Float64
) ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (agent_id, tool_name, event_date, hour);


CREATE MATERIALIZED VIEW IF NOT EXISTS agent_tool_usage_mv_view
TO agent_tool_usage_mv AS
SELECT
    agent_id,
    tool_name,
    if(properties != '', JSONExtractString(properties, 'tool_type'), 'unknown') AS tool_type,
    event_date,
    toStartOfHour(timestamp) AS hour,
    count() AS call_count,
    countIf(success = 1) AS success_count,
    countIf(success = 0) AS error_count,
    avg(latency_ms) AS avg_latency_ms,
    sum(latency_ms) AS total_latency_ms
FROM agent_event_logs
WHERE event_type = 'tool_call' AND tool_name != ''
GROUP BY agent_id, tool_name, tool_type, event_date, hour;


-- ============================================================
-- Agent Alerts Log
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_alerts (
    alert_id String,
    alert_type LowCardinality(String),
    agent_id String,
    severity LowCardinality(String),
    message String,
    trigger_data String DEFAULT '{}',
    auto_action LowCardinality(String) DEFAULT 'none',
    resolved UInt8 DEFAULT 0,
    resolved_by String DEFAULT '',
    timestamp DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC'),
    event_date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (agent_id, severity, timestamp)
TTL event_date + INTERVAL 180 DAY;


-- ============================================================
-- Agent Session Summary
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id String,
    agent_id String,
    agent_type LowCardinality(String),
    task_id String DEFAULT '',
    goal String DEFAULT '',
    status LowCardinality(String) DEFAULT 'executing',

    start_time DateTime64(3, 'UTC'),
    end_time Nullable(DateTime64(3, 'UTC')),
    duration_ms Nullable(Float64),

    total_events UInt32 DEFAULT 0,
    total_tool_calls UInt32 DEFAULT 0,
    total_llm_calls UInt32 DEFAULT 0,
    total_tokens UInt64 DEFAULT 0,
    total_cost_usd Float64 DEFAULT 0.0,

    error_count UInt32 DEFAULT 0,
    timeout_count UInt32 DEFAULT 0,
    anomaly_score Float32 DEFAULT 0.0,

    event_date Date DEFAULT toDate(start_time),
    created_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
) ENGINE = ReplacingMergeTree(created_at)
PARTITION BY toYYYYMM(event_date)
ORDER BY (agent_id, session_id);


-- ============================================================
-- Agent Daily Statistics
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_daily_stats (
    agent_id String,
    stat_date Date,

    total_events UInt64 DEFAULT 0,
    total_sessions UInt64 DEFAULT 0,
    total_tasks UInt64 DEFAULT 0,
    total_tool_calls UInt64 DEFAULT 0,
    total_llm_calls UInt64 DEFAULT 0,

    total_tokens UInt64 DEFAULT 0,
    total_cost_usd Float64 DEFAULT 0.0,

    avg_latency_ms Float64 DEFAULT 0.0,
    p95_latency_ms Float64 DEFAULT 0.0,
    success_rate Float64 DEFAULT 1.0,
    error_rate Float64 DEFAULT 0.0,

    anomaly_count UInt32 DEFAULT 0,
    alert_count UInt32 DEFAULT 0,

    updated_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
) ENGINE = ReplacingMergeTree(updated_at)
PARTITION BY toYYYYMM(stat_date)
ORDER BY (agent_id, stat_date);


-- ============================================================
-- Indexes for common queries
-- ============================================================
-- Trace lookup
-- SELECT * FROM agent_event_logs WHERE trace_id = 'xxx' ORDER BY timestamp

-- Agent activity timeline
-- SELECT * FROM agent_event_logs WHERE agent_id = 'xxx' AND event_date = today() ORDER BY timestamp

-- Cost analysis
-- SELECT agent_id, model_name, sum(cost_usd), sum(total_tokens) FROM agent_event_logs GROUP BY agent_id, model_name

-- Error analysis
-- SELECT agent_id, error_type, count() FROM agent_event_logs WHERE success = 0 GROUP BY agent_id, error_type
