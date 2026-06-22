"""Deterministic memory governance engine."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.contracts.memory import MemoryRecord
from aion_brain.contracts.memory_governance import (
    MemoryGovernanceAction,
    MemoryGovernanceDecision,
    MemoryGovernanceEvaluationRequest,
    MemoryGovernanceRule,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.memory_governance.repository import MemoryGovernanceRepository
from aion_brain.memory_governance.rules import default_memory_governance_rules
from aion_brain.policy.base import PolicyAdapter

_ACTION_PRECEDENCE: tuple[MemoryGovernanceAction, ...] = (
    "deny",
    "require_approval",
    "forget",
    "expire",
    "decay",
    "compact",
    "flag_conflict",
    "allow",
)
_ACTION_RULE_TYPES: dict[str, set[str]] = {
    "memory.write": {"write_gate"},
    "memory.retrieve": {"retrieval_gate"},
    "memory.update": {"write_gate", "retention"},
    "memory.forget": {"forgetting"},
    "memory.compact": {"compaction"},
    "memory.decay": {"decay", "retention"},
    "memory.conflict.scan": {"conflict_detection"},
}


class MemoryGovernanceEngine:
    """Evaluate generic memory governance rules."""

    def __init__(
        self,
        *,
        governance_repository: MemoryGovernanceRepository,
        risk_engine: object | None,
        approval_service: object | None,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None,
        settings: Settings,
    ) -> None:
        self._repository = governance_repository
        self._risk_engine = risk_engine
        self._approval_service = approval_service
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings

    def seed_default_rules(self) -> list[MemoryGovernanceRule]:
        """Seed generic default rules idempotently."""
        saved: list[MemoryGovernanceRule] = []
        for rule in default_memory_governance_rules():
            existing = self._repository.get_rule(rule.governance_rule_id)
            saved.append(existing or self._repository.save_rule(rule))
        return saved

    def create_rule(self, rule: MemoryGovernanceRule) -> MemoryGovernanceRule:
        """Create a governance rule after policy authorization."""
        decision = self._authorize(
            action_type="memory.governance.rule.create",
            resource_type="memory_governance_rule",
            resource_id=rule.governance_rule_id,
            risk_level="medium",
            scope=rule.owner_scope,
            context=rule.model_dump(mode="json"),
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        saved = self._repository.save_rule(rule)
        self._emit(
            "memory_governance_rule_created",
            "governance",
            saved.governance_rule_id,
            0.5,
            saved.governance_rule_id,
            {"rule_type": saved.rule_type, "action": saved.action},
        )
        return saved

    def list_rules(
        self,
        status: str | None = None,
        rule_type: str | None = None,
    ) -> list[MemoryGovernanceRule]:
        """List governance rules after read authorization."""
        decision = self._authorize(
            action_type="memory.governance.rule.read",
            resource_type="memory_governance_rule",
            resource_id=None,
            risk_level="low",
            scope=["workspace:main"],
            context={"status": status, "rule_type": rule_type},
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        return self._repository.list_rules(status=status, rule_type=rule_type)

    def disable_rule(
        self,
        governance_rule_id: str,
        reason: str | None,
        actor_id: str | None,
    ) -> MemoryGovernanceRule:
        """Disable one governance rule."""
        rule = self._repository.get_rule(governance_rule_id)
        if rule is None:
            raise ValueError("memory_governance_rule_not_found")
        decision = self._authorize(
            action_type="memory.governance.rule.disable",
            resource_type="memory_governance_rule",
            resource_id=governance_rule_id,
            risk_level="medium",
            scope=rule.owner_scope,
            context={"reason": reason, "actor_id": actor_id},
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        now = datetime.now(UTC)
        saved = self._repository.save_rule(
            rule.model_copy(
                update={
                    "status": "disabled",
                    "updated_at": now,
                    "disabled_at": now,
                    "metadata": {**rule.metadata, "disabled_reason": reason},
                }
            )
        )
        self._emit(
            "memory_governance_rule_disabled",
            "governance",
            saved.governance_rule_id,
            0.4,
            saved.governance_rule_id,
            {"reason": reason},
        )
        return saved

    def evaluate(
        self,
        request: MemoryGovernanceEvaluationRequest,
    ) -> MemoryGovernanceDecision:
        """Evaluate governance rules against one memory action."""
        if not self._settings.memory_governance_enabled:
            decision = _decision(
                request,
                [],
                "allow",
                "memory_governance_disabled",
                ["memory_governance_disabled"],
            )
            return self._repository.save_decision(decision)
        policy = self._authorize(
            action_type="memory.governance.evaluate",
            resource_type="memory",
            resource_id=request.memory.memory_id,
            risk_level="low",
            scope=request.owner_scope,
            context={
                "memory_id": request.memory.memory_id,
                "action_type": request.action_type,
            },
            trace_id=request.trace_id,
        )
        if not policy.allow:
            decision = _decision(
                request,
                [],
                "deny",
                policy.reason,
                policy.constraints or ["policy_denied"],
            )
            saved = self._repository.save_decision(decision)
            self._emit_decision(saved)
            return saved

        rules = [
            rule
            for rule in self._repository.list_rules(status="active")
            if _matches_rule(rule, request)
        ]
        selected_action = _selected_action(rules)
        decision = _decision(
            request,
            [rule.governance_rule_id for rule in rules],
            selected_action,
            _reason(selected_action, rules),
            [f"memory_governance_rule:{rule.governance_rule_id}" for rule in rules],
        )
        saved = self._repository.save_decision(decision)
        self._emit_decision(saved)
        return saved

    def _authorize(
        self,
        *,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
        scope: list[str],
        context: dict[str, Any],
        trace_id: str | None = None,
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=trace_id,
                actor_id=None,
                workspace_id=None,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=bool(context.get("approval_present")),
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )

    def _emit_decision(self, decision: MemoryGovernanceDecision) -> None:
        self._emit(
            "memory_governance_decision_recorded",
            "governance",
            decision.governance_decision_id,
            0.7,
            decision.trace_id or decision.governance_decision_id,
            {
                "memory_id": decision.memory_id,
                "decision": decision.decision,
                "rule_ids": decision.rule_ids,
            },
        )

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        trace_id: str,
        payload: dict[str, Any],
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{node_id}-{event_type}",
            trace_id=trace_id,
            event_type=cast(Any, event_type),
            node_type=cast(Any, node_type),
            node_id=node_id,
            edge_from=None,
            edge_to=node_id,
            intensity=max(0.0, min(1.0, intensity)),
            payload=payload,
            created_at=datetime.now(UTC),
        )
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


def _matches_rule(
    rule: MemoryGovernanceRule,
    request: MemoryGovernanceEvaluationRequest,
) -> bool:
    if rule.status != "active":
        return False
    if rule.rule_type not in _ACTION_RULE_TYPES.get(request.action_type, set()):
        return False
    memory = request.memory
    if rule.memory_types and memory.memory_type not in rule.memory_types:
        return False
    if rule.sensitivity_levels and memory.sensitivity not in rule.sensitivity_levels:
        return False
    if not _scope_matches(rule.owner_scope, request.owner_scope):
        return False
    return _conditions_match(rule, request)


def _conditions_match(
    rule: MemoryGovernanceRule,
    request: MemoryGovernanceEvaluationRequest,
) -> bool:
    memory = request.memory
    merged = {**memory.metadata, **request.context, **request.metadata}
    for key, expected in rule.conditions.items():
        if key == "confidence_below" and not memory.confidence < float(expected):
            return False
        if key == "age_days_above" and not _age_days(memory) > float(expected):
            return False
        if key == "sensitivity_in" and memory.sensitivity not in _string_set(expected):
            return False
        if key == "memory_type_in" and memory.memory_type not in _string_set(expected):
            return False
        if key == "source_event_missing" and bool(expected) and memory.source_event_id:
            return False
        if key == "content_ref_missing" and bool(expected) and memory.content_ref:
            return False
        if key == "evidence_ref_missing" and bool(expected) and _has_evidence_ref(memory):
            return False
        if key == "metadata_key_exists" and str(expected) not in merged:
            return False
        if key == "metadata_key_equals" and not _metadata_equals(merged, expected):
            return False
        if key == "stale_after_days" and not _age_days(memory) > float(expected):
            return False
        if key == "retrieval_score_below":
            score = merged.get("retrieval_score")
            if not isinstance(score, int | float) or not float(score) < float(expected):
                return False
    return True


def _selected_action(rules: list[MemoryGovernanceRule]) -> MemoryGovernanceAction:
    if not rules:
        return "allow"
    actions = {rule.action for rule in rules}
    for action in _ACTION_PRECEDENCE:
        if action in actions:
            return action
    return "allow"


def _decision(
    request: MemoryGovernanceEvaluationRequest,
    rules: list[str],
    action: MemoryGovernanceAction,
    reason: str,
    constraints: list[str],
) -> MemoryGovernanceDecision:
    return MemoryGovernanceDecision(
        governance_decision_id=f"memory-governance-decision-{uuid4().hex}",
        trace_id=request.trace_id,
        memory_id=request.memory.memory_id,
        rule_ids=rules,
        decision=action,
        reason=reason,
        constraints=constraints,
        metadata={
            "action_type": request.action_type,
            "memory_type": request.memory.memory_type,
            "sensitivity": request.memory.sensitivity,
        },
        created_at=datetime.now(UTC),
    )


def _reason(action: MemoryGovernanceAction, rules: list[MemoryGovernanceRule]) -> str:
    if not rules:
        return "no_governance_rule_matched"
    return f"memory_governance_{action}"


def _scope_matches(rule_scope: list[str], requested_scope: list[str]) -> bool:
    return "workspace:main" in rule_scope or bool(set(rule_scope) & set(requested_scope))


def _age_days(memory: MemoryRecord) -> float:
    created = memory.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return max(0.0, (datetime.now(UTC) - created).total_seconds() / 86400)


def _has_evidence_ref(memory: MemoryRecord) -> bool:
    refs = memory.metadata.get("evidence_refs")
    return bool(memory.content_ref or (isinstance(refs, list) and refs))


def _string_set(value: object) -> set[str]:
    if isinstance(value, list):
        return {str(item) for item in value}
    return {str(value)}


def _metadata_equals(metadata: dict[str, Any], expected: object) -> bool:
    if isinstance(expected, dict):
        key = expected.get("key")
        value = expected.get("value")
        return isinstance(key, str) and metadata.get(key) == value
    return False
