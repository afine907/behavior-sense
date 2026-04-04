"""
时间处理工具
"""
from datetime import datetime, timedelta, timezone
from typing import Optional


def utc_now() -> datetime:
    """获取当前 UTC 时间"""
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """转换为 UTC 时间"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_timestamp(dt: datetime) -> int:
    """转换为毫秒时间戳"""
    return int(dt.timestamp() * 1000)


def from_timestamp(ts: int) -> datetime:
    """从毫秒时间戳转换"""
    return datetime.fromtimestamp(ts / 1000, tz=timezone.utc)


def format_iso(dt: datetime) -> str:
    """格式化为 ISO 字符串"""
    return dt.isoformat()


def parse_iso(s: str) -> datetime:
    """解析 ISO 字符串"""
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def get_window_start(
    dt: datetime,
    window_size: timedelta,
) -> datetime:
    """获取时间窗口起始时间"""
    timestamp = dt.timestamp()
    window_seconds = window_size.total_seconds()
    window_start = (timestamp // window_seconds) * window_seconds
    return datetime.fromtimestamp(window_start, tz=dt.tzinfo or timezone.utc)


def get_window_end(
    dt: datetime,
    window_size: timedelta,
) -> datetime:
    """获取时间窗口结束时间"""
    return get_window_start(dt, window_size) + window_size


def is_in_window(
    dt: datetime,
    window_start: datetime,
    window_end: datetime,
) -> bool:
    """判断时间是否在窗口内"""
    return window_start <= dt < window_end


def get_time_buckets(
    start: datetime,
    end: datetime,
    bucket_size: timedelta,
) -> list[tuple[datetime, datetime]]:
    """获取时间分桶"""
    buckets = []
    current = get_window_start(start, bucket_size)

    while current < end:
        bucket_end = current + bucket_size
        buckets.append((current, min(bucket_end, end)))
        current = bucket_end

    return buckets


def humanize_duration(delta: timedelta) -> str:
    """人类可读的时间差"""
    total_seconds = int(delta.total_seconds())

    if total_seconds < 60:
        return f"{total_seconds}秒"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes}分钟"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours}小时"
    else:
        days = total_seconds // 86400
        return f"{days}天"


class TimeWindow:
    """时间窗口类"""

    def __init__(
        self,
        start: datetime,
        end: datetime,
    ):
        self.start = start
        self.end = end

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    def contains(self, dt: datetime) -> bool:
        return self.start <= dt < self.end

    def overlap(self, other: "TimeWindow") -> Optional["TimeWindow"]:
        """计算重叠窗口"""
        start = max(self.start, other.start)
        end = min(self.end, other.end)

        if start < end:
            return TimeWindow(start, end)
        return None

    def __repr__(self) -> str:
        return f"TimeWindow({self.start}, {self.end})"
