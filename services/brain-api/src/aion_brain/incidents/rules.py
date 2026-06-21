"""Incident correlation rule service."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.incidents import IncidentCorrelationRule
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry

_DEFAULT_RULES: tuple[tuple[str, str, str, list[str], list[str]], ...] = (
    ("same_trace_high_severity", "same_trace", "high", [], []),
    ("same_source_recent", "same_source", "medium", [], []),
    ("same_correlation_key_recent", "same_correlation_key", "low", [], []),
    (
        "prompt_model_grounding_cluster",
        "temporal_cluster",
        "medium",
        ["prompt_boundary", "model_output", "grounding"],
        [],
    ),
    (
        "run_timeout_cluster",
        "temporal_cluster",
        "medium",
        ["run_supervision"],
        ["stalled", "timed_out"],
    ),
    (
        "security_resilience_cluster",
        "temporal_cluster",
        "medium",
        ["security", "resilience"],
        [],
    ),
    ("audit_integrity_cluster", "temporal_cluster", "medium", ["audit"], ["verification_failed"]),
    (
        "release_freeze_cluster",
        "temporal_cluster",
        "medium",
        ["release", "freeze"],
        ["failed"],
    ),
)


class CorrelationRuleService:
    """Manage deterministic local incident correlation rules."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> CorrelationRuleService:
        return CorrelationRuleService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_rule(self, rule: IncidentCorrelationRule) -> IncidentCorrelationRule:
        authorize(
            self._policy_adapter,
            action_type="incident.rule.create",
            resource_type="incident_correlation_rule",
            resource_id=rule.correlation_rule_id,
            scope=rule.owner_scope,
            actor_id=rule.created_by or self._actor_context.actor_id,
            risk_level="medium",
        )
        stored = _save_rule(self._repository, rule)
        emit_telemetry(
            self._telemetry_service,
            event_type="incident_correlation_rule_created",
            node_type="correlation_rule",
            node_id=stored.correlation_rule_id,
            intensity=0.5,
            trace_id=self._actor_context.trace_id,
            payload={"rule_type": stored.rule_type, "status": stored.status},
        )
        return stored

    def list_rules(
        self,
        scope: list[str],
        status: str | None = None,
        rule_type: str | None = None,
        limit: int = 100,
    ) -> list[IncidentCorrelationRule]:
        authorize(
            self._policy_adapter,
            action_type="incident.rule.read",
            resource_type="incident_correlation_rule",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        list_rules = getattr(self._repository, "list_rules", None)
        if not callable(list_rules):
            return []
        return list(list_rules(scope=scope, status=status, rule_type=rule_type, limit=limit) or [])

    def disable_rule(
        self, correlation_rule_id: str, actor_id: str | None, reason: str
    ) -> IncidentCorrelationRule:
        rule = _require_rule(self._repository, correlation_rule_id)
        authorize(
            self._policy_adapter,
            action_type="incident.rule.update",
            resource_type="incident_correlation_rule",
            resource_id=correlation_rule_id,
            scope=rule.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        disabled = rule.model_copy(
            update={
                "status": "disabled",
                "disabled_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "metadata": {**rule.metadata, "disable_reason": reason},
            }
        )
        return _save_rule(self._repository, disabled)

    def seed_default_rules(self, scope: list[str], dry_run: bool = True) -> dict[str, object]:
        rules = [
            _default_rule(name, rule_type, severity, sources, signals, scope)
            for name, rule_type, severity, sources, signals in _DEFAULT_RULES
        ]
        if dry_run:
            return {
                "dry_run": True,
                "created": [],
                "rules": [rule.model_dump(mode="json") for rule in rules],
            }
        created = [self.create_rule(rule) for rule in rules]
        return {
            "dry_run": False,
            "created": [rule.correlation_rule_id for rule in created],
            "rules": [rule.model_dump(mode="json") for rule in created],
        }


def _default_rule(
    name: str,
    rule_type: str,
    severity: str,
    source_types: list[str],
    signal_types: list[str],
    scope: list[str],
) -> IncidentCorrelationRule:
    return IncidentCorrelationRule(
        correlation_rule_id=f"incident-rule-{name}",
        name=name,
        description=f"Default generic incident correlation rule: {name}.",
        status="active",
        rule_type=rule_type,  # type: ignore[arg-type]
        severity_threshold=severity,  # type: ignore[arg-type]
        source_types=source_types,  # type: ignore[arg-type]
        signal_types=signal_types,  # type: ignore[arg-type]
        window_seconds=3600,
        grouping_fields=["correlation_key"] if rule_type == "same_correlation_key" else [],
        conditions={"default_rule": True},
        owner_scope=scope,
        metadata={"seeded_by": "aion-069", "no_domain_logic": True},
        created_by="system",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _save_rule(repository: object, rule: IncidentCorrelationRule) -> IncidentCorrelationRule:
    save = getattr(repository, "save_rule", None)
    stored = save(rule) if callable(save) else rule
    return stored if isinstance(stored, IncidentCorrelationRule) else rule


def _require_rule(repository: object, correlation_rule_id: str) -> IncidentCorrelationRule:
    get = getattr(repository, "get_rule", None)
    rule = get(correlation_rule_id) if callable(get) else None
    if not isinstance(rule, IncidentCorrelationRule):
        raise ValueError("incident_correlation_rule_not_found")
    return rule


__all__ = ["CorrelationRuleService"]
