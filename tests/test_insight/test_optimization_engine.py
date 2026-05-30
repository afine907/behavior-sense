"""Tests for optimization engine"""
import pytest
from behavior_insight.optimization_engine import AgentOptimizationEngine


class TestOptimizationEngine:
    def setup_method(self):
        self.engine = AgentOptimizationEngine()

    def test_high_cost_suggestion(self):
        stats = {
            "agent_id": "test",
            "total_cost_usd": 100,
            "total_tasks": 10,
            "total_tokens": 500000,
            "total_cached_tokens": 0,
        }
        suggestions = self.engine.analyze(stats)
        assert any(s.category == "cost" for s in suggestions)

    def test_high_error_rate_suggestion(self):
        stats = {
            "agent_id": "test",
            "error_rate": 0.3,
        }
        suggestions = self.engine.analyze(stats)
        assert any("error" in s.title.lower() for s in suggestions)

    def test_no_suggestions_for_healthy_agent(self):
        stats = {
            "agent_id": "test",
            "total_cost_usd": 1,
            "total_tasks": 100,
            "total_tokens": 10000,
            "total_cached_tokens": 5000,
            "error_rate": 0.01,
            "p95_latency_ms": 500,
            "timeout_rate": 0.01,
            "retry_rate": 0.05,
        }
        suggestions = self.engine.analyze(stats)
        # Should have few or no suggestions
        assert len(suggestions) <= 2

    def test_generate_report(self):
        stats = {"agent_id": "test", "total_cost_usd": 100, "total_tasks": 1}
        suggestions = self.engine.analyze(stats)
        report = self.engine.generate_report("test", suggestions)
        assert "agent_id" in report
        assert "total_suggestions" in report
