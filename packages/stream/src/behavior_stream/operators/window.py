"""
窗口函数工具

实现滚动窗口、滑动窗口和会话窗口。
"""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Callable, Generator, Generic, TypeVar
from dataclasses import dataclass, field
from collections import defaultdict
import time

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class WindowResult(Generic[T]):
    """窗口结果"""
    window_start: datetime
    window_end: datetime
    key: str
    values: list[T] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class WindowFunction(ABC, Generic[T, R]):
    """窗口函数基类"""

    def __init__(
        self,
        window_size: timedelta,
        allowed_lateness: timedelta = timedelta(seconds=0),
    ):
        self.window_size = window_size
        self.allowed_lateness = allowed_lateness
        self._windows: dict[str, list[WindowResult[T]]] = defaultdict(list)

    @abstractmethod
    def get_window_start(self, timestamp: datetime) -> datetime:
        """获取窗口起始时间"""
        pass

    @abstractmethod
    def get_window_end(self, timestamp: datetime) -> datetime:
        """获取窗口结束时间"""
        pass

    @abstractmethod
    def assign_windows(self, timestamp: datetime) -> list[tuple[datetime, datetime]]:
        """为时间戳分配窗口"""
        pass

    def add_event(
        self,
        key: str,
        event: T,
        timestamp: datetime,
        extractor: Callable[[T], Any] | None = None,
    ) -> list[WindowResult[T]]:
        """添加事件到窗口"""
        windows = self.assign_windows(timestamp)
        results = []

        for window_start, window_end in windows:
            # 检查窗口是否已过期
            if datetime.utcnow() - window_end > self.allowed_lateness:
                continue

            # 查找或创建窗口
            window = self._find_or_create_window(key, window_start, window_end)
            window.values.append(event)
            results.append(window)

        return results

    def _find_or_create_window(
        self,
        key: str,
        window_start: datetime,
        window_end: datetime,
    ) -> WindowResult[T]:
        """查找或创建窗口"""
        for window in self._windows[key]:
            if window.window_start == window_start and window.window_end == window_end:
                return window

        window = WindowResult[T](
            window_start=window_start,
            window_end=window_end,
            key=key,
        )
        self._windows[key].append(window)
        return window

    def trigger_window(
        self,
        key: str,
        window_start: datetime,
        window_end: datetime,
    ) -> WindowResult[T] | None:
        """触发窗口并返回结果"""
        for i, window in enumerate(self._windows[key]):
            if window.window_start == window_start and window.window_end == window_end:
                return self._windows[key].pop(i)
        return None

    def get_expired_windows(self) -> Generator[tuple[str, WindowResult[T]], None, None]:
        """获取已过期的窗口"""
        now = datetime.utcnow()
        for key, windows in list(self._windows.items()):
            for window in windows[:]:
                if now > window.window_end + self.allowed_lateness:
                    yield key, window
                    windows.remove(window)

    def cleanup(self) -> int:
        """清理过期窗口"""
        count = 0
        for key, window in self.get_expired_windows():
            count += 1
        return count


class TumblingWindow(WindowFunction[T, R]):
    """
    滚动窗口

    窗口大小固定，窗口之间不重叠。
    示例: 每分钟统计一次，窗口大小为1分钟。
    """

    def __init__(
        self,
        window_size: timedelta,
        allowed_lateness: timedelta = timedelta(seconds=0),
        offset: timedelta = timedelta(seconds=0),
    ):
        super().__init__(window_size, allowed_lateness)
        self.offset = offset

    def get_window_start(self, timestamp: datetime) -> datetime:
        """获取窗口起始时间"""
        epoch = datetime(1970, 1, 1)
        total_seconds = (timestamp - epoch - self.offset).total_seconds()
        window_seconds = self.window_size.total_seconds()
        window_start_seconds = (total_seconds // window_seconds) * window_seconds
        return epoch + self.offset + timedelta(seconds=window_start_seconds)

    def get_window_end(self, timestamp: datetime) -> datetime:
        """获取窗口结束时间"""
        return self.get_window_start(timestamp) + self.window_size

    def assign_windows(self, timestamp: datetime) -> list[tuple[datetime, datetime]]:
        """分配窗口"""
        window_start = self.get_window_start(timestamp)
        window_end = window_start + self.window_size
        return [(window_start, window_end)]


class SlidingWindow(WindowFunction[T, R]):
    """
    滑动窗口

    窗口大小固定，窗口之间有重叠。
    示例: 每10秒计算过去1分钟的数据。

    - window_size: 窗口大小 (例如1分钟)
    - slide_interval: 滑动间隔 (例如10秒)
    """

    def __init__(
        self,
        window_size: timedelta,
        slide_interval: timedelta,
        allowed_lateness: timedelta = timedelta(seconds=0),
        offset: timedelta = timedelta(seconds=0),
    ):
        super().__init__(window_size, allowed_lateness)
        self.slide_interval = slide_interval
        self.offset = offset

        if slide_interval > window_size:
            raise ValueError("slide_interval must be less than or equal to window_size")

    def get_window_start(self, timestamp: datetime) -> datetime:
        """获取最近的窗口起始时间"""
        epoch = datetime(1970, 1, 1)
        total_seconds = (timestamp - epoch - self.offset).total_seconds()
        slide_seconds = self.slide_interval.total_seconds()
        window_start_seconds = (total_seconds // slide_seconds) * slide_seconds
        return epoch + self.offset + timedelta(seconds=window_start_seconds)

    def get_window_end(self, timestamp: datetime) -> datetime:
        """获取窗口结束时间"""
        return self.get_window_start(timestamp) + self.window_size

    def assign_windows(self, timestamp: datetime) -> list[tuple[datetime, datetime]]:
        """分配窗口 - 一个事件可能属于多个滑动窗口"""
        windows = []
        epoch = datetime(1970, 1, 1)
        slide_seconds = self.slide_interval.total_seconds()
        window_seconds = self.window_size.total_seconds()

        # 计算时间戳所在的滑动点
        total_seconds = (timestamp - epoch - self.offset).total_seconds()

        # 找到包含该时间戳的所有窗口
        # 最后一个可能的窗口起始点
        last_slide = (total_seconds // slide_seconds) * slide_seconds

        # 向前查找所有包含该时间戳的窗口
        current_slide = last_slide
        while current_slide > total_seconds - window_seconds:
            window_start = epoch + self.offset + timedelta(seconds=current_slide)
            window_end = window_start + self.window_size

            if window_start <= timestamp < window_end:
                windows.append((window_start, window_end))

            current_slide -= slide_seconds
            if current_slide < 0:
                break

        return windows


class SessionWindow(WindowFunction[T, R]):
    """
    会话窗口

    根据用户活动动态定义窗口，当会话超时时关闭窗口。
    示例: 用户操作间隔超过30秒则视为新会话。

    - timeout: 会话超时时间
    - max_session_length: 最大会话长度 (可选)
    """

    def __init__(
        self,
        timeout: timedelta,
        max_session_length: timedelta | None = None,
        allowed_lateness: timedelta = timedelta(seconds=0),
    ):
        # 会话窗口的 window_size 是动态的，这里用 timeout 代替
        super().__init__(timeout, allowed_lateness)
        self.timeout = timeout
        self.max_session_length = max_session_length
        self._last_activity: dict[str, datetime] = {}
        self._session_start: dict[str, datetime] = {}

    def get_window_start(self, timestamp: datetime) -> datetime:
        """会话窗口的起始时间是动态的"""
        return timestamp

    def get_window_end(self, timestamp: datetime) -> datetime:
        """会话窗口的结束时间是动态的"""
        return timestamp + self.timeout

    def assign_windows(self, timestamp: datetime) -> list[tuple[datetime, datetime]]:
        """会话窗口的分配是动态的"""
        # 这个方法在会话窗口中需要 key 信息，由 add_event_with_session 处理
        return []

    def add_event_with_session(
        self,
        key: str,
        event: T,
        timestamp: datetime,
    ) -> tuple[WindowResult[T], bool]:
        """
        添加事件到会话窗口

        返回 (窗口结果, 是否新会话)
        """
        is_new_session = False

        # 检查是否需要开始新会话
        if key in self._last_activity:
            last_time = self._last_activity[key]
            session_start = self._session_start[key]

            # 检查是否超时
            if timestamp - last_time > self.timeout:
                is_new_session = True
            # 检查是否超过最大会话长度
            elif self.max_session_length and timestamp - session_start > self.max_session_length:
                is_new_session = True

        if is_new_session or key not in self._last_activity:
            # 开始新会话
            is_new_session = True  # 标记为新会话
            self._session_start[key] = timestamp
            window = WindowResult[T](
                window_start=timestamp,
                window_end=timestamp + self.timeout,
                key=key,
            )
            self._windows[key].append(window)
        else:
            # 继续现有会话
            window = self._windows[key][-1]
            # 更新窗口结束时间
            window.window_end = timestamp + self.timeout

        # 更新最后活动时间
        self._last_activity[key] = timestamp

        # 添加事件
        window.values.append(event)

        return window, is_new_session

    def get_inactive_sessions(
        self,
        inactive_threshold: timedelta | None = None,
    ) -> Generator[tuple[str, WindowResult[T]], None, None]:
        """获取不活跃的会话"""
        if inactive_threshold is None:
            inactive_threshold = self.timeout

        now = datetime.utcnow()

        for key, windows in list(self._windows.items()):
            for window in windows[:]:
                if now - window.window_end > inactive_threshold:
                    yield key, window
                    windows.remove(window)

            # 清理会话状态
            if not windows:
                self._last_activity.pop(key, None)
                self._session_start.pop(key, None)

    def close_session(self, key: str) -> WindowResult[T] | None:
        """手动关闭会话"""
        if key in self._windows and self._windows[key]:
            window = self._windows[key].pop()
            self._last_activity.pop(key, None)
            self._session_start.pop(key, None)
            return window
        return None


# 聚合函数
class WindowAggregator:
    """窗口聚合器"""

    @staticmethod
    def count(values: list[Any]) -> int:
        """计数"""
        return len(values)

    @staticmethod
    def sum_float(values: list[Any], field: str) -> float:
        """求和"""
        return sum(v.get(field, 0) for v in values if isinstance(v, dict))

    @staticmethod
    def avg_float(values: list[Any], field: str) -> float:
        """平均值"""
        field_values = [v.get(field, 0) for v in values if isinstance(v, dict)]
        return sum(field_values) / len(field_values) if field_values else 0.0

    @staticmethod
    def min_float(values: list[Any], field: str) -> float:
        """最小值"""
        field_values = [v.get(field, 0) for v in values if isinstance(v, dict)]
        return min(field_values) if field_values else 0.0

    @staticmethod
    def max_float(values: list[Any], field: str) -> float:
        """最大值"""
        field_values = [v.get(field, 0) for v in values if isinstance(v, dict)]
        return max(field_values) if field_values else 0.0

    @staticmethod
    def distinct_count(values: list[Any], field: str) -> int:
        """去重计数"""
        field_values = {v.get(field) for v in values if isinstance(v, dict) and v.get(field) is not None}
        return len(field_values)
