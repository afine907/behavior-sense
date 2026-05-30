"""Tests for anomaly scorer"""
import pytest
from behavior_stream.anomaly_scorer import AgentAnomalyScorer


class TestAgentAnomalyScorer:
    def setup_method(self):
        self.scorer = AgentAnomalyScorer()

    def test_score_normal_event(self):
        event = {"agent_id": "test", "event_type": "tool_call", "latency_ms": 100, "success": True}
        result = self.scorer.score_event(event, [])
        assert 0 <= result["anomaly_score"] <= 1
        assert result["anomaly_level"] == "normal"

    def test_score_error_event(self):
        event = {"agent_id": "test", "event_type": "error", "success": False}
        result = self.scorer.score_event(event, [])
        assert result["anomaly_score"] > 0

    def test_score_with_alerts(self):
        event = {"agent_id": "test", "event_type": "tool_call"}
        alerts = [{"detector": "loop"}, {"detector": "loop"}]
        result = self.scorer.score_event(event, alerts)
        assert result["anomaly_score"] > 0.2

    def test_score_high_latency(self):
        event = {"agent_id": "test", "latency_ms": 25000}
        result = self.scorer.score_event(event, [])
        assert result["anomaly_score"] > 0.1

    def test_agent_trend(self):
        # Add multiple events
        for i in range(10):
            event = {"agent_id": "test", "latency_ms": 100 * (i + 1), "success": True}
            self.scorer.score_event(event, [])

        trend = self.scorer.get_agent_trend("test")
        assert trend["sample_count"] == 10

    def test_all_agents_scores(self):
        self.scorer.score_event({"agent_id": "a1"}, [])
        self.scorer.score_event({"agent_id": "a2"}, [])

        scores = self.scorer.get_all_agents_scores()
        assert len(scores) == 2
