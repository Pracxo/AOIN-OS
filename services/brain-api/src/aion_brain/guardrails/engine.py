"""Deterministic generic guardrail engine."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.contracts.guardrails import GuardrailDecision, GuardrailRule
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.risk import RiskAssessment
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.guardrails.defaults import default_guardrail_rules
from aion_brain.guardrails.repository import GuardrailRepository
from aion_brain.policy.base import PolicyAdapter

_SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


class GuardrailEngine:
    """Evaluate generic guardrail rules against a risk assessment."""

    def __init__(
        self,
        *,
        repository: GuardrailRepository,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings

    def ensure_default_rules(self) -> None:
        """Seed default generic rules idempotently."""
        for rule in default_guardrail_rules():
            if self._repository.get_rule(rule.guardrail_id) is None:
                self._repository.save_rule(rule)

    def create_rule(self, rule: GuardrailRule) -> GuardrailRule:
        """Create or update one guardrail rule after policy authorization."""
        decision = self._authorize(
            action_type="guardrail.rule.create",
            resource_type="guardrail_rule",
            resource_id=rule.guardrail_id,
            risk_level=rule.severity,
            scope=rule.scope,
            approval_present=True,
            context=rule.model_dump(mode="json"),
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        saved = self._repository.save_rule(rule)
        self._emit_rule(saved)
        return saved

    def list_rules(self, *, status: str | None = None) -> list[GuardrailRule]:
        """List guardrail rules after policy authorization."""
        decision = self._authorize(
            action_type="guardrail.rule.read",
            resource_type="guardrail_rule",
            resource_id=None,
            risk_level="low",
            scope=["workspace:main"],
            approval_present=False,
            context={"status": status},
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        return self._repository.list_rules(status=status)

    def disable_rule(
        self,
        guardrail_id: str,
        *,
        actor_id: str | None = None,
    ) -> GuardrailRule:
        """Disable a guardrail rule through the policy boundary."""
        rule = self._repository.get_rule(guardrail_id)
        if rule is None:
            raise ValueError("guardrail_rule_not_found")
        decision = self._authorize(
            action_type="guardrail.rule.disable",
            resource_type="guardrail_rule",
            resource_id=guardrail_id,
            risk_level=rule.severity,
            scope=rule.scope,
            approval_present=True,
            context={"actor_id": actor_id},
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        now = datetime.now(UTC)
        return self._repository.save_rule(
            rule.model_copy(update={"status": "disabled", "updated_at": now, "disabled_at": now})
        )

    def evaluate(self, risk: RiskAssessment) -> GuardrailDecision:
        """Evaluate matching guardrails and persist the decision."""
        decision = self._authorize(
            action_type="guardrail.evaluate",
            resource_type=risk.resource_type,
            resource_id=risk.resource_id,
            risk_level=risk.computed_risk_level,
            scope=_scope(risk),
            approval_present=bool(risk.metadata.get("approval_present")),
            context={
                "risk_assessment_id": risk.risk_assessment_id,
                "action_type": risk.action_type,
                **risk.metadata,
            },
        )
        if not decision.allow and not decision.approval_required:
            guardrail_decision = _decision(
                risk,
                matched=[],
                blocked=True,
                approval_required=False,
                severity="critical",
                reason=decision.reason,
                constraints=decision.constraints,
            )
            return self._save_and_emit(guardrail_decision)
        if not self._settings.guardrails_enabled:
            guardrail_decision = _decision(
                risk,
                matched=[],
                blocked=False,
                approval_required=False,
                severity="low",
                reason="guardrails_disabled",
                constraints=["guardrails_disabled"],
            )
            return self._save_and_emit(guardrail_decision)

        self.ensure_default_rules()
        rules = [
            rule
            for rule in self._repository.list_rules(status="active")
            if _matches_rule(rule, risk)
        ]
        blocked = any(rule.effect == "block" for rule in rules)
        approval_required = any(rule.effect == "require_approval" for rule in rules)
        severity = _highest_severity(rules) if rules else risk.computed_risk_level
        reason = _reason(blocked, approval_required, rules)
        constraints = [f"guardrail:{rule.guardrail_id}" for rule in rules]
        if blocked:
            constraints.append("blocked_by_guardrail")
        elif approval_required:
            constraints.append("approval_required")
        guardrail_decision = _decision(
            risk,
            matched=[rule.guardrail_id for rule in rules],
            blocked=blocked,
            approval_required=approval_required,
            severity=severity,
            reason=reason,
            constraints=constraints,
        )
        return self._save_and_emit(guardrail_decision)

    def _authorize(
        self,
        *,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
        scope: list[str],
        approval_present: bool,
        context: dict[str, object],
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=approval_present,
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )

    def _save_and_emit(self, decision: GuardrailDecision) -> GuardrailDecision:
        saved = self._repository.save_decision(decision)
        self._emit_decision(saved)
        return saved

    def _emit_rule(self, rule: GuardrailRule) -> None:
        self._emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{rule.guardrail_id}-created",
                trace_id=rule.guardrail_id,
                event_type="guardrail_rule_created",
                node_type="guardrail",
                node_id=rule.guardrail_id,
                edge_from=None,
                edge_to=rule.guardrail_id,
                intensity=0.5,
                payload={
                    "effect": rule.effect,
                    "severity": rule.severity,
                    "owner_scope": rule.scope,
                },
                created_at=datetime.now(UTC),
            )
        )

    def _emit_decision(self, decision: GuardrailDecision) -> None:
        self._emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{decision.guardrail_decision_id}-evaluated",
                trace_id=decision.trace_id or decision.guardrail_decision_id,
                event_type="guardrail_blocked" if decision.blocked else "guardrail_evaluated",
                node_type="guardrail",
                node_id=decision.guardrail_decision_id,
                edge_from=decision.risk_assessment_id,
                edge_to=decision.guardrail_decision_id,
                intensity=0.9 if decision.blocked else 0.6,
                payload={
                    "allow": decision.allow,
                    "approval_required": decision.approval_required,
                    "blocked": decision.blocked,
                    "matched_guardrails": decision.matched_guardrails,
                    "owner_scope": _metadata_scope(decision.metadata),
                },
                created_at=datetime.now(UTC),
            )
        )

    def _emit(self, event: VisualTelemetryEvent) -> None:
        if self._telemetry_service is None:
            return
        try:
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
                return
            save = getattr(self._telemetry_service, "save_visual_telemetry", None)
            if callable(save):
                save(event.trace_id, [event])
        except Exception:
            return


def _matches_rule(rule: GuardrailRule, risk: RiskAssessment) -> bool:
    if rule.status != "active":
        return False
    if not _list_matches(rule.action_types, risk.action_type):
        return False
    if not _list_matches(rule.resource_types, risk.resource_type):
        return False
    if risk.computed_risk_level not in rule.risk_levels:
        return False
    if not _scope_matches(rule.scope, _scope(risk)):
        return False
    for key, expected in rule.conditions.items():
        if risk.metadata.get(key) != expected:
            return False
    return True


def _list_matches(patterns: list[str], value: str) -> bool:
    return "*" in patterns or value in patterns


def _scope_matches(rule_scope: list[str], request_scope: list[str]) -> bool:
    return "workspace:main" in rule_scope or bool(set(rule_scope) & set(request_scope))


def _highest_severity(rules: list[GuardrailRule]) -> str:
    return max((rule.severity for rule in rules), key=lambda item: _SEVERITY_ORDER[item])


def _reason(blocked: bool, approval_required: bool, rules: list[GuardrailRule]) -> str:
    if blocked:
        return "guardrail_blocked"
    if approval_required:
        return "guardrail_requires_approval"
    if rules:
        return "guardrail_allowed"
    return "no_guardrail_matched"


def _decision(
    risk: RiskAssessment,
    *,
    matched: list[str],
    blocked: bool,
    approval_required: bool,
    severity: str,
    reason: str,
    constraints: list[str],
) -> GuardrailDecision:
    return GuardrailDecision(
        guardrail_decision_id=f"guardrail-decision-{uuid4().hex}",
        trace_id=risk.trace_id,
        risk_assessment_id=risk.risk_assessment_id,
        action_type=risk.action_type,
        resource_type=risk.resource_type,
        resource_id=risk.resource_id,
        matched_guardrails=matched,
        allow=not blocked and not approval_required,
        approval_required=approval_required,
        blocked=blocked,
        severity=cast(Any, severity),
        reason=reason,
        constraints=constraints,
        metadata=risk.metadata,
        created_at=datetime.now(UTC),
    )


def _scope(risk: RiskAssessment) -> list[str]:
    value = risk.metadata.get("security_scope")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    if risk.workspace_id:
        return [f"workspace:{risk.workspace_id}"]
    return ["workspace:main"]


def _metadata_scope(metadata: dict[str, object]) -> list[str]:
    value = metadata.get("security_scope")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return ["workspace:main"]
