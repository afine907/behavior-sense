"""
behavior_stream 模块单元测试
"""
import pytest
from datetime import datetime, timedelta, timezone

from behavior_stream.operators.window import (
    WindowResult,
    TumblingWindow,
    SlidingWindow,
    SessionWindow,
    WindowAggregator,
)


class TestWindowResult:
    """窗口结果测试"""

    def test_create_window_result(self):
        """测试创建窗口结果"""
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 13, 0, 0)

        result = WindowResult(
            window_start=start,
            window_end=end,
            key="user_001",
        )

        assert result.window_start == start
        assert result.window_end == end
        assert result.key == "user_001"
        assert result.values == []

    def test_window_result_with_values(self):
        """测试带值的窗口结果"""
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 13, 0, 0)

        result = WindowResult(
            window_start=start,
            window_end=end,
            key="user_001",
            values=[{"amount": 100}, {"amount": 200}],
        )

        assert len(result.values) == 2


class TestTumblingWindow:
    """滚动窗口测试"""

    @pytest.fixture
    def window(self):
        return TumblingWindow(
            window_size=timedelta(hours=1),
        )

    def test_create_tumbling_window(self, window):
        """测试创建滚动窗口"""
        assert window.window_size == timedelta(hours=1)

    def test_get_window_start(self, window):
        """测试获取窗口起始时间"""
        dt = datetime(2024, 1, 1, 12, 35, 0)
        start = window.get_window_start(dt)

        assert start.minute == 0
        assert start.hour == 12

    def test_get_window_end(self, window):
        """测试获取窗口结束时间"""
        dt = datetime(2024, 1, 1, 12, 35, 0)
        end = window.get_window_end(dt)

        assert end.hour == 13
        assert end.minute == 0

    def test_assign_windows(self, window):
        """测试分配窗口"""
        dt = datetime(2024, 1, 1, 12, 35, 0)
        windows = window.assign_windows(dt)

        assert len(windows) == 1
        start, end = windows[0]
        assert start.hour == 12
        assert end.hour == 13

    def test_add_event(self, window):
        """测试添加事件"""
        # 使用当前时间确保窗口未过期
        dt = datetime.utcnow()
        event = {"amount": 100}

        results = window.add_event("user_001", event, dt)

        assert len(results) == 1
        assert len(results[0].values) == 1

    def test_trigger_window(self, window):
        """测试触发窗口"""
        # 使用当前时间确保窗口未过期
        dt = datetime.utcnow()
        event = {"amount": 100}

        window.add_event("user_001", event, dt)

        # 计算实际的窗口边界
        start = window.get_window_start(dt)
        end = window.get_window_end(dt)

        triggered = window.trigger_window("user_001", start, end)
        assert triggered is not None
        assert len(triggered.values) == 1

    def test_window_with_offset(self):
        """测试带偏移的窗口"""
        window = TumblingWindow(
            window_size=timedelta(hours=1),
            offset=timedelta(minutes=30),
        )

        dt = datetime(2024, 1, 1, 12, 45, 0)
        start = window.get_window_start(dt)

        # 偏移 30 分钟后，窗口起始应该是 12:30
        assert start.minute == 30


class TestSlidingWindow:
    """滑动窗口测试"""

    @pytest.fixture
    def window(self):
        return SlidingWindow(
            window_size=timedelta(minutes=5),
            slide_interval=timedelta(minutes=1),
        )

    def test_create_sliding_window(self, window):
        """测试创建滑动窗口"""
        assert window.window_size == timedelta(minutes=5)
        assert window.slide_interval == timedelta(minutes=1)

    def test_invalid_slide_interval(self):
        """测试无效的滑动间隔"""
        with pytest.raises(ValueError):
            SlidingWindow(
                window_size=timedelta(minutes=1),
                slide_interval=timedelta(minutes=5),
            )

    def test_assign_windows_overlapping(self, window):
        """测试重叠窗口分配"""
        dt = datetime.utcnow()
        windows = window.assign_windows(dt)

        # 5分钟窗口，1分钟滑动，事件可能属于多个窗口
        assert len(windows) >= 1

    def test_add_event_to_multiple_windows(self, window):
        """测试事件添加到多个窗口"""
        dt = datetime.utcnow()
        event = {"amount": 100}

        results = window.add_event("user_001", event, dt)

        # 事件可能被添加到多个窗口
        assert len(results) >= 1


class TestSessionWindow:
    """会话窗口测试"""

    @pytest.fixture
    def window(self):
        return SessionWindow(
            timeout=timedelta(minutes=5),
        )

    def test_create_session_window(self, window):
        """测试创建会话窗口"""
        assert window.timeout == timedelta(minutes=5)

    def test_new_session(self):
        """测试新会话"""
        # 创建新的窗口实例避免测试间干扰
        window = SessionWindow(timeout=timedelta(minutes=5))
        dt = datetime.utcnow()
        event = {"action": "click"}

        result, is_new = window.add_event_with_session("user_test_new", event, dt)

        assert is_new is True
        assert len(result.values) == 1

    def test_continue_session(self, window):
        """测试继续会话"""
        base = datetime.utcnow()
        dt1 = base
        dt2 = base + timedelta(minutes=2)

        event1 = {"action": "click"}
        event2 = {"action": "purchase"}

        window.add_event_with_session("user_continue", event1, dt1)
        result, is_new = window.add_event_with_session("user_continue", event2, dt2)

        # 间隔 2 分钟，小于 5 分钟超时，应该是同一会话
        assert is_new is False
        assert len(result.values) == 2

    def test_session_timeout(self, window):
        """测试会话超时"""
        base = datetime.utcnow()
        dt1 = base
        dt2 = base + timedelta(minutes=10)

        event1 = {"action": "click"}
        event2 = {"action": "purchase"}

        window.add_event_with_session("user_timeout", event1, dt1)
        result, is_new = window.add_event_with_session("user_timeout", event2, dt2)

        # 间隔 10 分钟，大于 5 分钟超时，应该是新会话
        assert is_new is True

    def test_max_session_length(self):
        """测试最大会话长度"""
        window = SessionWindow(
            timeout=timedelta(minutes=5),
            max_session_length=timedelta(minutes=10),
        )

        base = datetime.utcnow()
        dt1 = base
        dt2 = base + timedelta(minutes=8)  # 8 分钟后

        event1 = {"action": "click"}
        event2 = {"action": "purchase"}

        window.add_event_with_session("user_max_length", event1, dt1)
        result, is_new = window.add_event_with_session("user_max_length", event2, dt2)

        # 超过最大会话长度，应该是新会话
        assert is_new is True

    def test_close_session(self, window):
        """测试关闭会话"""
        dt = datetime.utcnow()
        event = {"action": "click"}

        window.add_event_with_session("user_close", event, dt)
        closed = window.close_session("user_close")

        assert closed is not None
        assert len(closed.values) == 1


class TestTumblingWindowAdvanced:
    """滚动窗口高级测试"""

    def test_expired_window_cleanup(self):
        """测试过期窗口清理"""
        window = TumblingWindow(
            window_size=timedelta(hours=1),
            allowed_lateness=timedelta(minutes=5),
        )

        # 先添加一个当前事件
        dt = datetime.utcnow()
        event = {"amount": 100}
        window.add_event("user_001", event, dt)

        # 直接操作窗口数据模拟过期
        # 将窗口结束时间设为过去
        for key, windows in window._windows.items():
            for w in windows:
                w.window_end = datetime.utcnow() - timedelta(hours=1)

        # 清理过期窗口
        cleaned = window.cleanup()
        assert cleaned == 1

    def test_late_event_rejected(self):
        """测试迟到事件被拒绝"""
        window = TumblingWindow(
            window_size=timedelta(hours=1),
            allowed_lateness=timedelta(minutes=0),  # 不允许迟到
        )

        # 添加一个明显过期的事件（窗口结束时间在过去）
        dt = datetime.utcnow() - timedelta(hours=2)
        event = {"amount": 100}
        results = window.add_event("user_001", event, dt)

        # 迟到事件应该被拒绝（窗口已过期）
        assert len(results) == 0

    def test_window_with_lateness_allowed(self):
        """测试允许迟到事件"""
        window = TumblingWindow(
            window_size=timedelta(hours=1),
            allowed_lateness=timedelta(minutes=30),
        )

        # 添加一个迟到但在允许范围内的事件
        dt = datetime.utcnow() - timedelta(minutes=10)
        event = {"amount": 100}
        results = window.add_event("user_001", event, dt)

        # 应该被接受
        assert len(results) == 1


class TestSessionWindowAdvanced:
    """会话窗口高级测试"""

    def test_get_inactive_sessions(self):
        """测试获取不活跃会话"""
        window = SessionWindow(timeout=timedelta(minutes=5))

        # 创建一个会话
        dt = datetime.utcnow()
        event = {"action": "click"}
        window.add_event_with_session("user_inactive", event, dt)

        # 手动设置窗口结束时间为过去
        for key, windows in window._windows.items():
            for w in windows:
                w.window_end = datetime.utcnow() - timedelta(minutes=10)

        # 获取不活跃会话
        inactive = list(window.get_inactive_sessions())
        assert len(inactive) == 1
        assert inactive[0][0] == "user_inactive"


class TestWindowAggregator:
    """窗口聚合器测试"""

    def test_count(self):
        """测试计数"""
        values = [{"a": 1}, {"a": 2}, {"a": 3}]
        assert WindowAggregator.count(values) == 3

    def test_sum_float(self):
        """测试求和"""
        values = [{"amount": 100}, {"amount": 200}, {"amount": 300}]
        result = WindowAggregator.sum_float(values, "amount")
        assert result == 600.0

    def test_avg_float(self):
        """测试平均值"""
        values = [{"amount": 100}, {"amount": 200}, {"amount": 300}]
        result = WindowAggregator.avg_float(values, "amount")
        assert result == 200.0

    def test_min_float(self):
        """测试最小值"""
        values = [{"amount": 100}, {"amount": 200}, {"amount": 300}]
        result = WindowAggregator.min_float(values, "amount")
        assert result == 100.0

    def test_max_float(self):
        """测试最大值"""
        values = [{"amount": 100}, {"amount": 200}, {"amount": 300}]
        result = WindowAggregator.max_float(values, "amount")
        assert result == 300.0

    def test_distinct_count(self):
        """测试去重计数"""
        values = [
            {"user_id": "user_001"},
            {"user_id": "user_002"},
            {"user_id": "user_001"},
        ]
        result = WindowAggregator.distinct_count(values, "user_id")
        assert result == 2

    def test_empty_values(self):
        """测试空值"""
        assert WindowAggregator.count([]) == 0
        assert WindowAggregator.sum_float([], "amount") == 0.0
        assert WindowAggregator.avg_float([], "amount") == 0.0
