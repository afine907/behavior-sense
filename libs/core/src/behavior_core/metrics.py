"""
指标收集系统
"""
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass
class Counter:
    """计数器"""
    name: str
    value: float = 0.0
    labels: dict[str, str] = field(default_factory=dict)

    def inc(self, amount: float = 1.0) -> None:
        self.value += amount

    def reset(self) -> None:
        self.value = 0.0


@dataclass
class Gauge:
    """仪表盘"""
    name: str
    value: float = 0.0
    labels: dict[str, str] = field(default_factory=dict)

    def set(self, value: float) -> None:
        self.value = value

    def inc(self, amount: float = 1.0) -> None:
        self.value += amount

    def dec(self, amount: float = 1.0) -> None:
        self.value -= amount


@dataclass
class Histogram:
    """直方图"""
    name: str
    buckets: list[float] = field(default_factory=lambda: [
        0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0
    ])
    counts: dict[float, int] = field(default_factory=dict)
    sum_value: float = 0.0
    count: int = 0

    def __post_init__(self):
        for bucket in self.buckets:
            self.counts[bucket] = 0

    def observe(self, value: float) -> None:
        self.sum_value += value
        self.count += 1
        for bucket in self.buckets:
            if value <= bucket:
                self.counts[bucket] += 1

    @property
    def avg(self) -> float:
        return self.sum_value / self.count if self.count > 0 else 0.0


class MetricsRegistry:
    """指标注册表"""

    def __init__(self):
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}

    def counter(self, name: str, labels: dict[str, str] | None = None) -> Counter:
        """获取或创建计数器"""
        key = self._make_key(name, labels)
        if key not in self._counters:
            self._counters[key] = Counter(name=name, labels=labels or {})
        return self._counters[key]

    def gauge(self, name: str, labels: dict[str, str] | None = None) -> Gauge:
        """获取或创建仪表盘"""
        key = self._make_key(name, labels)
        if key not in self._gauges:
            self._gauges[key] = Gauge(name=name, labels=labels or {})
        return self._gauges[key]

    def histogram(self, name: str, labels: dict[str, str] | None = None) -> Histogram:
        """获取或创建直方图"""
        key = self._make_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = Histogram(name=name, labels=labels or {})
        return self._histograms[key]

    def _make_key(self, name: str, labels: dict[str, str] | None) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_all_metrics(self) -> dict[str, Any]:
        """获取所有指标"""
        return {
            "counters": {
                k: {"name": v.name, "value": v.value, "labels": v.labels}
                for k, v in self._counters.items()
            },
            "gauges": {
                k: {"name": v.name, "value": v.value, "labels": v.labels}
                for k, v in self._gauges.items()
            },
            "histograms": {
                k: {
                    "name": v.name,
                    "count": v.count,
                    "sum": v.sum_value,
                    "avg": v.avg,
                    "labels": v.labels,
                }
                for k, v in self._histograms.items()
            },
        }

    def reset(self) -> None:
        """重置所有指标"""
        for c in self._counters.values():
            c.reset()
        for g in self._gauges.values():
            g.set(0)
        self._histograms.clear()


# Global metrics registry
_metrics = MetricsRegistry()


def get_metrics() -> MetricsRegistry:
    """获取全局指标注册表"""
    return _metrics


# Pre-defined metrics
class AgentMetrics:
    """Agent相关指标"""

    def __init__(self, registry: MetricsRegistry | None = None):
        self._registry = registry or get_metrics()

    @property
    def events_processed(self) -> Counter:
        return self._registry.counter("agent_events_processed_total")

    @property
    def events_failed(self) -> Counter:
        return self._registry.counter("agent_events_failed_total")

    @property
    def alerts_generated(self) -> Counter:
        return self._registry.counter("agent_alerts_generated_total")

    @property
    def cost_tracked(self) -> Counter:
        return self._registry.counter("agent_cost_tracked_usd")

    @property
    def tokens_processed(self) -> Counter:
        return self._registry.counter("agent_tokens_processed_total")

    @property
    def active_agents(self) -> Gauge:
        return self._registry.gauge("agent_active_count")

    @property
    def processing_latency(self) -> Histogram:
        return self._registry.histogram("agent_processing_latency_seconds")

    @property
    def detection_latency(self) -> Histogram:
        return self._registry.histogram("agent_detection_latency_seconds")

    def record_event(self, agent_id: str, event_type: str, latency_ms: float) -> None:
        """记录事件处理"""
        self.events_processed.inc()
        self.processing_latency.observe(latency_ms / 1000)

    def record_alert(self, alert_type: str, severity: str) -> None:
        """记录告警"""
        self.alerts_generated.inc()

    def record_cost(self, agent_id: str, cost_usd: float) -> None:
        """记录成本"""
        self.cost_tracked.inc(cost_usd)

    def record_tokens(self, agent_id: str, tokens: int) -> None:
        """记录Token使用"""
        self.tokens_processed.inc(tokens)


# Service info tracking
_service_info: dict[str, str] = {}


def set_service_info(name: str, version: str) -> None:
    """设置服务信息（用于指标导出）"""
    global _service_info
    _service_info = {"name": name, "version": version}


def get_service_info() -> dict[str, str]:
    """获取服务信息"""
    return dict(_service_info)


def metrics_to_prometheus_string() -> str:
    """将指标导出为Prometheus格式字符串"""
    lines = []

    # Service info
    if _service_info:
        lines.append(f'# HELP service_info Service information')
        lines.append(f'# TYPE service_info gauge')
        labels = ",".join(f'{k}="{v}"' for k, v in _service_info.items())
        lines.append(f'service_info{{{labels}}} 1')
        lines.append("")

    # Counters
    for key, counter in _metrics._counters.items():
        labels = ""
        if counter.labels:
            label_str = ",".join(f'{k}="{v}"' for k, v in sorted(counter.labels.items()))
            labels = f"{{{label_str}}}"
        lines.append(f'# TYPE {counter.name} counter')
        lines.append(f'{counter.name}{labels} {counter.value}')

    # Gauges
    for key, gauge in _metrics._gauges.items():
        labels = ""
        if gauge.labels:
            label_str = ",".join(f'{k}="{v}"' for k, v in sorted(gauge.labels.items()))
            labels = f"{{{label_str}}}"
        lines.append(f'# TYPE {gauge.name} gauge')
        lines.append(f'{gauge.name}{labels} {gauge.value}')

    # Histograms
    for key, histogram in _metrics._histograms.items():
        labels = ""
        if histogram.labels:
            label_str = ",".join(f'{k}="{v}"' for k, v in sorted(histogram.labels.items()))
            labels = f"{{{label_str}}}"
        lines.append(f'# TYPE {histogram.name} histogram')
        for bucket, count in sorted(histogram.counts.items()):
            bucket_labels = f'le="{bucket}"'
            if labels:
                bucket_labels = f"{labels[:-1]},{bucket_labels}}}"
            else:
                bucket_labels = f"{{{bucket_labels}}}"
            lines.append(f'{histogram.name}_bucket{bucket_labels} {count}')
        lines.append(f'{histogram.name}_sum{labels} {histogram.sum_value}')
        lines.append(f'{histogram.name}_count{labels} {histogram.count}')

    return "\n".join(lines)
