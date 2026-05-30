"""Tests for compliance checker"""
import pytest
from behavior_insight.compliance_checker import AgentComplianceChecker, ComplianceStatus


class TestComplianceChecker:
    def setup_method(self):
        self.checker = AgentComplianceChecker()

    def test_compliant_agent(self):
        stats = {"cost_1d": 10, "daily_budget": 100}
        profile = {"model_name": "gpt-4", "has_injection_guard": True}
        tags = {}

        report = self.checker.check("test", stats, profile, tags)
        assert report.overall_status == ComplianceStatus.COMPLIANT

    def test_cost_violation(self):
        stats = {"cost_1d": 150, "daily_budget": 100}
        report = self.checker.check("test", stats)
        assert report.violations > 0

    def test_unapproved_model(self):
        stats = {"model_name": "unknown-model"}
        report = self.checker.check("test", stats)
        assert report.violations > 0

    def test_pii_without_audit(self):
        tags = {"pii_accessor": {"value": "true"}}
        report = self.checker.check("test", {}, tags=tags)
        assert report.violations > 0

    def test_report_structure(self):
        report = self.checker.check("test", {})
        assert report.agent_id == "test"
        assert report.total_rules > 0
        assert len(report.results) > 0
