-- BehaviorSense 数据库初始化脚本

-- 创建用户画像表
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id VARCHAR(64) PRIMARY KEY,
    basic_info JSONB DEFAULT '{}',
    behavior_tags JSONB DEFAULT '[]',
    stat_tags JSONB DEFAULT '{}',
    predict_tags JSONB DEFAULT '{}',
    risk_level VARCHAR(16) DEFAULT 'low',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建用户统计表
CREATE TABLE IF NOT EXISTS user_stats (
    user_id VARCHAR(64) PRIMARY KEY,
    total_events BIGINT DEFAULT 0,
    total_sessions BIGINT DEFAULT 0,
    total_purchases BIGINT DEFAULT 0,
    total_amount DECIMAL(12, 2) DEFAULT 0,
    events_1d BIGINT DEFAULT 0,
    events_7d BIGINT DEFAULT 0,
    events_30d BIGINT DEFAULT 0,
    purchases_1d BIGINT DEFAULT 0,
    purchases_7d BIGINT DEFAULT 0,
    purchases_30d BIGINT DEFAULT 0,
    amount_1d DECIMAL(12, 2) DEFAULT 0,
    amount_7d DECIMAL(12, 2) DEFAULT 0,
    amount_30d DECIMAL(12, 2) DEFAULT 0,
    last_event_time TIMESTAMP,
    last_purchase_time TIMESTAMP,
    last_login_time TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建审核工单表
CREATE TABLE IF NOT EXISTS audit_orders (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    rule_id VARCHAR(64) NOT NULL,
    trigger_data JSONB DEFAULT '{}',
    audit_level VARCHAR(16) DEFAULT 'MEDIUM',
    status VARCHAR(16) DEFAULT 'pending',
    assignee VARCHAR(64),
    reviewer_note TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建规则定义表
CREATE TABLE IF NOT EXISTS rules (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    condition TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    enabled BOOLEAN DEFAULT TRUE,
    actions JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',
    version INTEGER DEFAULT 1,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_profiles_risk_level ON user_profiles(risk_level);
CREATE INDEX IF NOT EXISTS idx_user_stats_update_time ON user_stats(update_time);
CREATE INDEX IF NOT EXISTS idx_audit_orders_status ON audit_orders(status);
CREATE INDEX IF NOT EXISTS idx_audit_orders_assignee ON audit_orders(assignee);
CREATE INDEX IF NOT EXISTS idx_audit_orders_create_time ON audit_orders(create_time);
CREATE INDEX IF NOT EXISTS idx_rules_enabled ON rules(enabled);
CREATE INDEX IF NOT EXISTS idx_rules_priority ON rules(priority);

-- 更新时间触发器
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.update_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_profiles_timestamp
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_user_stats_timestamp
    BEFORE UPDATE ON user_stats
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_audit_orders_timestamp
    BEFORE UPDATE ON audit_orders
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_rules_timestamp
    BEFORE UPDATE ON rules
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
