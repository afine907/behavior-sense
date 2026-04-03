"""
Faust 应用配置

定义 Faust 应用、Topic 和状态存储。
"""
import faust
from datetime import timedelta
from behavior_core.config.settings import get_settings

settings = get_settings()

# 创建 Faust 应用
app = faust.App(
    id="behavior-sense-stream",
    broker=settings.pulsar_url,
    store="rocksdb://./data/state",
    topic_replication_factor=1,
    topic_partitions=4,
    processing_guarantee="at_least_once",
    stream_wait_empty=False,
    stream_publish_on_commit=True,
    table_standby_replicas=0,
    broker_session_timeout=timedelta(seconds=30),
    broker_heartbeat_interval=timedelta(seconds=10),
)

# 定义 Topic
user_behavior_topic = app.topic(
    settings.pulsar_topic("user-behavior"),
    value_type=str,  # JSON string
    key_type=str,
    partitions=4,
    retention=timedelta(days=7),
    compacting=False,
)

aggregation_result_topic = app.topic(
    settings.pulsar_topic("aggregation-result"),
    value_type=str,
    key_type=str,
    partitions=4,
    retention=timedelta(days=30),
    compacting=True,
)

alerts_topic = app.topic(
    settings.pulsar_topic("alerts"),
    value_type=str,
    key_type=str,
    partitions=4,
    retention=timedelta(days=7),
    compacting=False,
)

rules_topic = app.topic(
    settings.pulsar_topic("rule-match-result"),
    value_type=str,
    key_type=str,
    partitions=4,
    retention=timedelta(days=7),
    compacting=False,
)

# 定义状态存储表
user_stats_table = app.Table(
    "user_stats",
    default=dict,
    partitions=4,
    key_type=str,
    value_type=dict,
)

user_login_failures = app.Table(
    "user_login_failures",
    default=list,
    partitions=4,
    key_type=str,
    value_type=list,
)

user_event_window = app.Table(
    "user_event_window",
    default=dict,
    partitions=4,
    key_type=str,
    value_type=dict,
)
