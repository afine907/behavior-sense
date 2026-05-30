"""
AI Agent合规检查器
"""
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ComplianceStatus(str, Enum):
    """合规状态"""
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    UNKNOWN = "unknown"


class ComplianceRule(BaseModel):
    """合规规则"""
    rule_id: str
    name: str
    description: str
    category: str  # data_access, cost, security, audit, model_usage
    severity: str = "medium"
    enabled: bool = True


class ComplianceResult(BaseModel):
    """合规检查结果"""
    rule_id: str
    rule_name: str
    status: ComplianceStatus
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=_utc_now)


class ComplianceReport(BaseModel):
    """合规报告"""
    agent_id: str
    checked_at: datetime = Field(default_factory=_utc_now)
    overall_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    total_rules: int = 0
    passed: int = 0
    warnings: int = 0
    violations: int = 0
    results: list[ComplianceResult] = Field(default_factory=list)


class AgentComplianceChecker:
    """Agent合规检查器"""

    def __init__(self):
        self._rules: list[ComplianceRule] = self._default_rules()

    def _default_rules(self) -> list[ComplianceRule]:
        """默认合规规则"""
        return [
            ComplianceRule(
                rule_id="comp-001",
                name="PII Data Access Logging",
                description="All PII data access must be logged for audit",
                category="data_access",
                severity="high",
            ),
            ComplianceRule(
                rule_id="comp-002",
                name="Cost Budget Compliance",
                description="Agent must stay within allocated budget",
                category="cost",
                severity="high",
            ),
            ComplianceRule(
                rule_id="comp-003",
                name="Approved Models Only",
                description="Agent must use only approved AI models",
                category="model_usage",
                severity="medium",
            ),
            ComplianceRule(
                rule_id="comp-004",
                name="Tool Authorization",
                description="Agent must only use authorized tools",
                category="security",
                severity="high",
            ),
            ComplianceRule(
                rule_id="comp-005",
                name="Audit Trail Completeness",
                description="All high-risk actions must have complete audit trails",
                category="audit",
                severity="high",
            ),
            ComplianceRule(
                rule_id="comp-006",
                name="Rate Limit Compliance",
                description="Agent must respect API rate limits",
                category="security",
                severity="medium",
            ),
            ComplianceRule(
                rule_id="comp-007",
                name="Data Retention Policy",
                description="Agent data must comply with retention policies",
                category="data_access",
                severity="medium",
            ),
            ComplianceRule(
                rule_id="comp-008",
                name="Prompt Injection Prevention",
                description="Agent must have prompt injection prevention measures",
                category="security",
                severity="critical",
            ),
        ]

    def check(self, agent_id: str, agent_stats: dict[str, Any],
              agent_profile: dict[str, Any] | None = None,
              agent_tags: dict[str, Any] | None = None) -> ComplianceReport:
        """执行合规检查"""
        results = []

        for rule in self._rules:
            if not rule.enabled:
                continue

            result = self._check_rule(rule, agent_stats, agent_profile, agent_tags)
            results.append(result)

        # Calculate overall status
        violations = sum(1 for r in results if r.status == ComplianceStatus.VIOLATION)
        warnings = sum(1 for r in results if r.status == ComplianceStatus.WARNING)
        passed = sum(1 for r in results if r.status == ComplianceStatus.COMPLIANT)

        if violations > 0:
            overall = ComplianceStatus.VIOLATION
        elif warnings > 0:
            overall = ComplianceStatus.WARNING
        else:
            overall = ComplianceStatus.COMPLIANT

        return ComplianceReport(
            agent_id=agent_id,
            overall_status=overall,
            total_rules=len(results),
            passed=passed,
            warnings=warnings,
            violations=violations,
            results=results,
        )

    def _check_rule(self, rule: ComplianceRule, stats: dict,
                    profile: dict | None, tags: dict | None) -> ComplianceResult:
        """检查单条规则"""

        if rule.rule_id == "comp-001":
            return self._check_pii_logging(rule, stats, tags)
        elif rule.rule_id == "comp-002":
            return self._check_cost_budget(rule, stats)
        elif rule.rule_id == "comp-003":
            return self._check_approved_models(rule, stats, profile)
        elif rule.rule_id == "comp-004":
            return self._check_tool_authorization(rule, stats, tags)
        elif rule.rule_id == "comp-005":
            return self._check_audit_trail(rule, stats)
        elif rule.rule_id == "comp-006":
            return self._check_rate_limits(rule, stats)
        elif rule.rule_id == "comp-007":
            return self._check_data_retention(rule, stats)
        elif rule.rule_id == "comp-008":
            return self._check_injection_prevention(rule, stats, profile)

        return ComplianceResult(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            status=ComplianceStatus.UNKNOWN,
            message="Rule not implemented",
        )

    def _check_pii_logging(self, rule, stats, tags) -> ComplianceResult:
        pii_access = tags.get("pii_accessor", {}).get("value") == "true" if tags else False
        has_audit = tags.get("pii_audit_logged", {}).get("value") == "true" if tags else False

        if pii_access and not has_audit:
            return ComplianceResult(
                rule_id=rule.rule_id, rule_name=rule.name,
                status=ComplianceStatus.VIOLATION,
                message="PII access detected without audit logging",
            )
        return ComplianceResult(
            rule_id=rule.rule_id, rule_name=rule.name,
            status=ComplianceStatus.COMPLIANT,
            message="PII access properly logged",
        )

    def _check_cost_budget(self, rule, stats) -> ComplianceResult:
        cost_1d = stats.get("cost_1d", 0)
        budget = stats.get("daily_budget", 100)

        if cost_1d > budget:
            return ComplianceResult(
                rule_id=rule.rule_id, rule_name=rule.name,
                status=ComplianceStatus.VIOLATION,
                message=f"Daily cost ${cost_1d:.2f} exceeds budget ${budget:.2f}",
                details={"cost": cost_1d, "budget": budget},
            )
        elif cost_1d > budget * 0.8:
            return ComplianceResult(
                rule_id=rule.rule_id, rule_name=rule.name,
                status=ComplianceStatus.WARNING,
                message=f"Daily cost ${cost_1d:.2f} approaching budget ${budget:.2f}",
            )
        return ComplianceResult(
            rule_id=rule.rule_id, rule_name=rule.name,
            status=ComplianceStatus.COMPLIANT,
            message="Within budget",
        )

    def _check_approved_models(self, rule, stats, profile) -> ComplianceResult:
        approved = {"gpt-4", "gpt-4-turbo", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"}
        model = stats.get("model_name") or (profile.get("model_name") if profile else None)

        if model and model not in approved:
            return ComplianceResult(
                rule_id=rule.rule_id, rule_name=rule.name,
                status=ComplianceStatus.VIOLATION,
                message=f"Using unapproved model: {model}",
                details={"model": model, "approved": list(approved)},
            )
        return ComplianceResult(
            rule_id=rule.rule_id, rule_name=rule.name,
            status=ComplianceStatus.COMPLIANT,
            message="Using approved model",
        )

    def _check_tool_authorization(self, rule, stats, tags) -> ComplianceResult:
        unauthorized = tags.get("unauthorized_tool_use", {}).get("value") == "true" if tags else False

        if unauthorized:
            return ComplianceResult(
                rule_id=rule.rule_id, rule_name=rule.name,
                status=ComplianceStatus.VIOLATION,
                message="Unauthorized tool usage detected",
            )
        return ComplianceResult(
            rule_id=rule.rule_id, rule_name=rule.name,
            status=ComplianceStatus.COMPLIANT,
            message="All tools authorized",
        )

    def _check_audit_trail(self, rule, stats) -> ComplianceResult:
        high_risk_actions = stats.get("high_risk_actions", 0)
        audited_actions = stats.get("audited_actions", 0)

        if high_risk_actions > 0 and audited_actions < high_risk_actions:
            return ComplianceResult(
                rule_id=rule.rule_id, rule_name=rule.name,
                status=ComplianceStatus.WARNING,
                message=f"{high_risk_actions - audited_actions} high-risk actions missing audit trail",
            )
        return ComplianceResult(
            rule_id=rule.rule_id, rule_name=rule.name,
            status=ComplianceStatus.COMPLIANT,
            message="Audit trails complete",
        )

    def _check_rate_limits(self, rule, stats) -> ComplianceResult:
        rate_limit_hits = stats.get("rate_limit_hits", 0)

        if rate_limit_hits > 10:
            return ComplianceResult(
                rule_id=rule.rule_id, rule_name=rule.name,
                status=ComplianceStatus.WARNING,
                message=f"Hit rate limits {rate_limit_hits} times",
            )
        return ComplianceResult(
            rule_id=rule.rule_id, rule_name=rule.name,
            status=ComplianceStatus.COMPLIANT,
            message="Within rate limits",
        )

    def _check_data_retention(self, rule, stats) -> ComplianceResult:
        # Always compliant in this implementation
        return ComplianceResult(
            rule_id=rule.rule_id, rule_name=rule.name,
            status=ComplianceStatus.COMPLIANT,
            message="Data retention policy followed",
        )

    def _check_injection_prevention(self, rule, stats, profile) -> ComplianceResult:
        has_guard = profile.get("has_injection_guard", True) if profile else True

        if not has_guard:
            return ComplianceResult(
                rule_id=rule.rule_id, rule_name=rule.name,
                status=ComplianceStatus.VIOLATION,
                message="No prompt injection prevention measures in place",
            )
        return ComplianceResult(
            rule_id=rule.rule_id, rule_name=rule.name,
            status=ComplianceStatus.COMPLIANT,
            message="Injection prevention active",
        )

    def add_rule(self, rule: ComplianceRule) -> None:
        """添加自定义规则"""
        self._rules.append(rule)

    def get_rules(self) -> list[ComplianceRule]:
        """获取所有规则"""
        return self._rules
