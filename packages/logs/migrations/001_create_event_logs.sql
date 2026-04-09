-- ClickHouse Event Logs Table
-- BehaviorSense 事件日志存储

CREATE DATABASE IF NOT EXISTS behavior_sense;

CREATE TABLE IF NOT EXISTS behavior_sense.event_logs (
    -- 主键和分区
    event_id        String,
    event_date      Date,              -- 分区键，从 timestamp 提取

    -- 核心字段
    user_id         String,
    event_type      LowCardinality(String),
    timestamp       DateTime64(3),     -- 毫秒精度

    -- 会话和来源
    session_id      String,
    page_url        String,
    referrer        String,

    -- 设备信息
    user_agent      String,
    ip_address      String,

    -- 扩展属性
    properties      String,            -- JSON 字符串

    -- 元数据
    ingested_at     DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, event_type, timestamp, event_id)
TTL event_date + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;

-- 索引优化
ALTER TABLE behavior_sense.event_logs ADD INDEX IF NOT EXISTS idx_event_id event_id TYPE bloom_filter(0.01) GRANULARITY 4;
ALTER TABLE behavior_sense.event_logs ADD INDEX IF NOT EXISTS idx_user_id user_id TYPE bloom_filter(0.01) GRANULARITY 4;
ALTER TABLE behavior_sense.event_logs ADD INDEX IF NOT EXISTS idx_session_id session_id TYPE bloom_filter(0.01) GRANULARITY 4;

-- 物化视图：小时级统计
CREATE MATERIALIZED VIEW IF NOT EXISTS behavior_sense.event_stats_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (hour, event_type)
AS SELECT
    toStartOfHour(timestamp) as hour,
    event_type,
    count() as event_count,
    uniqExact(user_id) as unique_users
FROM behavior_sense.event_logs
GROUP BY hour, event_type;
