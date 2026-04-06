"""
behavior_core 模块单元测试
"""
import pytest
from datetime import datetime, timedelta, timezone

from behavior_core.models.event import (
    EventType,
    UserBehavior,
    StandardEvent,
    AggregationResult,
    AlertEvent,
)
from behavior_core.models.user import (
    UserStatus,
    UserLevel,
    TagSource,
    TagValue,
    UserTags,
    UserProfile,
    UserStat,
)
from behavior_core.utils.datetime import (
    utc_now,
    to_utc,
    to_timestamp,
    from_timestamp,
    format_iso,
    parse_iso,
    get_window_start,
    get_window_end,
    is_in_window,
    get_time_buckets,
    humanize_duration,
    TimeWindow,
)


class TestEventType:
    """事件类型枚举测试"""

    def test_event_type_values(self):
        """测试事件类型值"""
        assert EventType.VIEW == "view"
        assert EventType.CLICK == "click"
        assert EventType.PURCHASE == "purchase"
        assert EventType.SEARCH == "search"
        assert EventType.COMMENT == "comment"
        assert EventType.LOGIN == "login"
        assert EventType.LOGOUT == "logout"
        assert EventType.REGISTER == "register"
        assert EventType.FAVORITE == "favorite"
        assert EventType.SHARE == "share"

    def test_event_type_is_string(self):
        """测试事件类型是字符串枚举"""
        assert isinstance(EventType.VIEW.value, str)

    def test_event_type_count(self):
        """测试事件类型总数"""
        assert len(EventType) == 10


class TestUserStatus:
    """用户状态枚举测试"""

    def test_user_status_values(self):
        """测试用户状态值"""
        assert UserStatus.ACTIVE == "active"
        assert UserStatus.INACTIVE == "inactive"
        assert UserStatus.SUSPENDED == "suspended"
        assert UserStatus.DELETED == "deleted"


class TestUserLevel:
    """用户等级枚举测试"""

    def test_user_level_values(self):
        """测试用户等级值"""
        assert UserLevel.NEW == "new"
        assert UserLevel.NORMAL == "normal"
        assert UserLevel.VIP == "vip"
        assert UserLevel.SVIP == "svip"


class TestUserBehavior:
    """用户行为事件模型测试"""

    def test_create_user_behavior(self):
        """测试创建用户行为事件"""
        event = UserBehavior(
            user_id="user_001",
            event_type=EventType.VIEW,
        )
        assert event.user_id == "user_001"
        assert event.event_type == EventType.VIEW
        assert event.event_id is not None
        assert event.timestamp is not None

    def test_user_behavior_with_properties(self):
        """测试带属性的用户行为事件"""
        event = UserBehavior(
            user_id="user_001",
            event_type=EventType.PURCHASE,
            properties={"amount": 100.0, "product_id": "p_001"},
        )
        assert event.properties["amount"] == 100.0
        assert event.properties["product_id"] == "p_001"

    def test_user_behavior_default_values(self):
        """测试默认值"""
        event = UserBehavior(
            user_id="user_001",
            event_type=EventType.VIEW,
        )
        assert event.session_id is None
        assert event.page_url is None
        assert event.properties == {}

    def test_user_behavior_json_encoding(self):
        """测试 JSON 编码"""
        event = UserBehavior(
            user_id="user_001",
            event_type=EventType.VIEW,
        )
        json_data = event.model_dump()
        assert "event_id" in json_data
        assert "timestamp" in json_data


class TestStandardEvent:
    """标准化事件模型测试"""

    def test_create_standard_event(self):
        """测试创建标准化事件"""
        event = StandardEvent(
            event_id="evt_001",
            user_id="user_001",
            event_type="view",
            timestamp=datetime.now(timezone.utc),
        )
        assert event.event_id == "evt_001"
        assert event.tags == []

    def test_standard_event_with_tags(self):
        """测试带标签的标准化事件"""
        event = StandardEvent(
            event_id="evt_001",
            user_id="user_001",
            event_type="purchase",
            timestamp=datetime.now(timezone.utc),
            tags=["high_value", "vip"],
        )
        assert len(event.tags) == 2
        assert "high_value" in event.tags


class TestAggregationResult:
    """聚合结果模型测试"""

    def test_create_aggregation_result(self):
        """测试创建聚合结果"""
        result = AggregationResult(
            user_id="user_001",
            window_start=datetime.now(timezone.utc),
            window_end=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        assert result.event_count == 0
        assert result.purchase_count == 0
        assert result.total_amount == 0.0

    def test_aggregation_result_with_data(self):
        """测试带数据的聚合结果"""
        result = AggregationResult(
            user_id="user_001",
            window_start=datetime.now(timezone.utc),
            window_end=datetime.now(timezone.utc) + timedelta(hours=1),
            event_count=100,
            view_count=80,
            click_count=15,
            purchase_count=5,
            total_amount=500.0,
            unique_sessions=10,
        )
        assert result.event_count == 100
        assert result.total_amount == 500.0


class TestAlertEvent:
    """告警事件模型测试"""

    def test_create_alert_event(self):
        """测试创建告警事件"""
        alert = AlertEvent(
            alert_type="high_frequency",
            user_id="user_001",
            message="用户访问频率异常",
        )
        assert alert.alert_id is not None
        assert alert.severity == "medium"
        assert alert.resolved is False

    def test_alert_event_severity(self):
        """测试告警严重级别"""
        alert = AlertEvent(
            alert_type="fraud_suspected",
            user_id="user_001",
            message="疑似欺诈行为",
            severity="critical",
        )
        assert alert.severity == "critical"


class TestUserTags:
    """用户标签模型测试"""

    def test_create_user_tags(self):
        """测试创建用户标签"""
        user_tags = UserTags(user_id="user_001")
        assert user_tags.user_id == "user_001"
        assert user_tags.tags == {}

    def test_set_tag(self):
        """测试设置标签"""
        user_tags = UserTags(user_id="user_001")
        user_tags.set_tag("level", "vip", TagSource.RULE)
        assert user_tags.get_tag("level").value == "vip"
        assert user_tags.get_tag("level").source == TagSource.RULE

    def test_remove_tag(self):
        """测试移除标签"""
        user_tags = UserTags(user_id="user_001")
        user_tags.set_tag("level", "vip")
        assert user_tags.remove_tag("level") is True
        assert user_tags.get_tag("level") is None

    def test_remove_nonexistent_tag(self):
        """测试移除不存在的标签"""
        user_tags = UserTags(user_id="user_001")
        assert user_tags.remove_tag("nonexistent") is False

    def test_tag_confidence(self):
        """测试标签置信度"""
        user_tags = UserTags(user_id="user_001")
        user_tags.set_tag("risk", "high", confidence=0.85)
        assert user_tags.get_tag("risk").confidence == 0.85

    def test_get_nonexistent_tag(self):
        """测试获取不存在的标签"""
        user_tags = UserTags(user_id="user_001")
        assert user_tags.get_tag("nonexistent") is None

    def test_multiple_tags(self):
        """测试多个标签"""
        user_tags = UserTags(user_id="user_001")
        user_tags.set_tag("level", "vip")
        user_tags.set_tag("risk", "low")
        user_tags.set_tag("segment", "premium")
        assert len(user_tags.tags) == 3


class TestTagValue:
    """标签值模型测试"""

    def test_create_tag_value(self):
        """测试创建标签值"""
        tag = TagValue(value="vip")
        assert tag.value == "vip"
        assert tag.confidence == 1.0
        assert tag.source == TagSource.AUTO

    def test_tag_value_with_all_fields(self):
        """测试带所有字段的标签值"""
        expire_at = datetime(2024, 12, 31, 23, 59, 59)
        tag = TagValue(
            value="high_risk",
            confidence=0.95,
            source=TagSource.RULE,
            expire_at=expire_at,
        )
        assert tag.value == "high_risk"
        assert tag.confidence == 0.95
        assert tag.source == TagSource.RULE
        assert tag.expire_at == expire_at


class TestTagSource:
    """标签来源枚举测试"""

    def test_tag_source_values(self):
        """测试标签来源值"""
        assert TagSource.AUTO == "AUTO"
        assert TagSource.MANUAL == "MANUAL"
        assert TagSource.AUDIT == "AUDIT"
        assert TagSource.RULE == "RULE"
        assert TagSource.IMPORT == "IMPORT"


class TestUserProfile:
    """用户画像模型测试"""

    def test_create_user_profile(self):
        """测试创建用户画像"""
        profile = UserProfile(user_id="user_001")
        assert profile.user_id == "user_001"
        assert profile.risk_level == "low"
        assert profile.behavior_tags == []

    def test_user_profile_with_data(self):
        """测试带数据的用户画像"""
        profile = UserProfile(
            user_id="user_001",
            basic_info={"age": 25, "city": "Beijing"},
            behavior_tags=["high_value", "frequent_buyer"],
            risk_level="medium",
        )
        assert profile.basic_info["age"] == 25
        assert len(profile.behavior_tags) == 2


class TestUserStat:
    """用户统计模型测试"""

    def test_create_user_stat(self):
        """测试创建用户统计"""
        stat = UserStat(user_id="user_001")
        assert stat.total_events == 0
        assert stat.total_purchases == 0
        assert stat.total_amount == 0.0

    def test_user_stat_with_data(self):
        """测试带数据的用户统计"""
        stat = UserStat(
            user_id="user_001",
            total_events=1000,
            total_purchases=50,
            total_amount=5000.0,
            events_7d=200,
            purchases_7d=10,
        )
        assert stat.total_events == 1000
        assert stat.events_7d == 200


class TestDatetimeUtils:
    """时间工具测试"""

    def test_utc_now(self):
        """测试获取 UTC 时间"""
        now = utc_now()
        assert now.tzinfo == timezone.utc

    def test_to_utc(self):
        """测试转换为 UTC 时间"""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        utc_dt = to_utc(dt)
        assert utc_dt.tzinfo == timezone.utc

    def test_timestamp_conversion(self):
        """测试时间戳转换"""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        ts = to_timestamp(dt)
        converted = from_timestamp(ts)
        assert converted.year == dt.year
        assert converted.month == dt.month
        assert converted.day == dt.day

    def test_format_iso(self):
        """测试 ISO 格式化"""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        iso_str = format_iso(dt)
        assert "2024-01-01" in iso_str

    def test_parse_iso(self):
        """测试 ISO 解析"""
        iso_str = "2024-01-01T12:00:00Z"
        dt = parse_iso(iso_str)
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1

    def test_get_window_start(self):
        """测试获取窗口起始时间"""
        dt = datetime(2024, 1, 1, 12, 35, 0, tzinfo=timezone.utc)
        window_start = get_window_start(dt, timedelta(hours=1))
        assert window_start.minute == 0
        assert window_start.hour == 12

    def test_get_window_end(self):
        """测试获取窗口结束时间"""
        dt = datetime(2024, 1, 1, 12, 35, 0, tzinfo=timezone.utc)
        window_end = get_window_end(dt, timedelta(hours=1))
        assert window_end.hour == 13
        assert window_end.minute == 0

    def test_is_in_window(self):
        """测试判断时间是否在窗口内"""
        start = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        dt_inside = datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc)
        dt_outside = datetime(2024, 1, 1, 13, 30, 0, tzinfo=timezone.utc)

        assert is_in_window(dt_inside, start, end) is True
        assert is_in_window(dt_outside, start, end) is False

    def test_get_time_buckets(self):
        """测试获取时间分桶"""
        start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc)
        buckets = get_time_buckets(start, end, timedelta(hours=1))

        assert len(buckets) == 3
        assert buckets[0][0] == start
        assert buckets[2][1] == end

    def test_humanize_duration(self):
        """测试人类可读时间差"""
        assert humanize_duration(timedelta(seconds=30)) == "30秒"
        assert humanize_duration(timedelta(minutes=5)) == "5分钟"
        assert humanize_duration(timedelta(hours=2)) == "2小时"
        assert humanize_duration(timedelta(days=3)) == "3天"


class TestTimeWindow:
    """时间窗口类测试"""

    def test_create_time_window(self):
        """测试创建时间窗口"""
        start = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        window = TimeWindow(start, end)

        assert window.start == start
        assert window.end == end
        assert window.duration == timedelta(hours=1)

    def test_contains(self):
        """测试包含判断"""
        start = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        window = TimeWindow(start, end)

        inside = datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc)
        outside = datetime(2024, 1, 1, 13, 30, 0, tzinfo=timezone.utc)

        assert window.contains(inside) is True
        assert window.contains(outside) is False

    def test_overlap(self):
        """测试重叠计算"""
        w1 = TimeWindow(
            datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
        )
        w2 = TimeWindow(
            datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 15, 0, 0, tzinfo=timezone.utc),
        )

        overlap = w1.overlap(w2)
        assert overlap is not None
        assert overlap.duration == timedelta(hours=1)

    def test_no_overlap(self):
        """测试无重叠"""
        w1 = TimeWindow(
            datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        )
        w2 = TimeWindow(
            datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 15, 0, 0, tzinfo=timezone.utc),
        )

        overlap = w1.overlap(w2)
        assert overlap is None
