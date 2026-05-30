"""
指标测试
"""
import pytest
from behavior_core.metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsRegistry,
    AgentMetrics,
)


class TestCounter:
    def test_increment(self):
        c = Counter(name="test")
        c.inc()
        assert c.value == 1.0
        c.inc(5)
        assert c.value == 6.0

    def test_reset(self):
        c = Counter(name="test")
        c.inc(10)
        c.reset()
        assert c.value == 0.0


class TestGauge:
    def test_set(self):
        g = Gauge(name="test")
        g.set(42)
        assert g.value == 42

    def test_inc_dec(self):
        g = Gauge(name="test")
        g.inc(5)
        assert g.value == 5
        g.dec(2)
        assert g.value == 3


class TestHistogram:
    def test_observe(self):
        h = Histogram(name="test")
        h.observe(0.5)
        h.observe(1.5)
        assert h.count == 2
        assert h.avg == 1.0

    def test_buckets(self):
        h = Histogram(name="test")
        h.observe(0.001)  # < 0.005
        h.observe(0.01)   # < 0.025
        h.observe(5.0)    # < 10.0
        assert h.count == 3


class TestMetricsRegistry:
    def test_counter_creation(self):
        registry = MetricsRegistry()
        c = registry.counter("test")
        assert c.name == "test"
        c.inc()
        assert c.value == 1

    def test_gauge_creation(self):
        registry = MetricsRegistry()
        g = registry.gauge("test")
        g.set(42)
        assert g.value == 42

    def test_histogram_creation(self):
        registry = MetricsRegistry()
        h = registry.histogram("test")
        h.observe(1.0)
        assert h.count == 1

    def test_get_all_metrics(self):
        registry = MetricsRegistry()
        registry.counter("c1").inc()
        registry.gauge("g1").set(42)

        metrics = registry.get_all_metrics()
        assert "counters" in metrics
        assert "gauges" in metrics


class TestAgentMetrics:
    def test_record_event(self):
        metrics = AgentMetrics()
        metrics.record_event("agent-1", "tool_call", 150)
        assert metrics.events_processed.value == 1

    def test_record_alert(self):
        metrics = AgentMetrics()
        metrics.record_alert("loop", "high")
        assert metrics.alerts_generated.value == 1

    def test_record_cost(self):
        metrics = AgentMetrics()
        metrics.record_cost("agent-1", 1.5)
        assert metrics.cost_tracked.value == 1.5
