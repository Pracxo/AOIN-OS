"""Compatibility rule service and default rule catalog."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from aion_brain.contracts.compatibility import CompatibilityRule
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry

DEFAULT_RULE_TYPES = (
    "no_removed_required_field",
    "no_removed_route",
    "no_removed_sdk_method",
    "no_removed_cli_command",
    "no_removed_policy_action",
    "no_removed_env_setting",
    "no_removed_telemetry_event",
    "no_removed_registry_resource",
    "no_type_narrowing",
    "no_visibility_leak",
    "no_secret_schema",
    "no_domain_interface",
)


class CompatibilityRuleService:
    """Manage deterministic compatibility rule records."""

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

    def with_actor_context(self, actor_context: ActorContext) -> CompatibilityRuleService:
        return CompatibilityRuleService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_rule(self, rule: CompatibilityRule) -> CompatibilityRule:
        authorize(
            self._policy_adapter,
            action_type="contract_registry.rule.create",
            resource_type="compatibility_rule",
            resource_id=rule.compatibility_rule_id,
            scope=rule.owner_scope,
            actor_id=rule.created_by or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
        )
        save = getattr(self._repository, "save_rule", None)
        stored = save(rule) if callable(save) else rule
        emit_telemetry(
            self._telemetry_service,
            event_type="compatibility_rule_created",
            node_type="compatibility_rule",
            node_id=stored.compatibility_rule_id,
            intensity=0.4,
            trace_id=self._actor_context.trace_id,
            payload={"rule_type": stored.rule_type},
        )
        return stored

    def list_rules(
        self,
        scope: list[str],
        status: str | None = None,
        rule_type: str | None = None,
        limit: int = 100,
    ) -> list[CompatibilityRule]:
        authorize(
            self._policy_adapter,
            action_type="contract_registry.rule.read",
            resource_type="compatibility_rule",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_items = getattr(self._repository, "list_rules", None)
        items = (
            list_items(status=status, rule_type=rule_type, limit=limit)
            if callable(list_items)
            else []
        )
        return [item for item in items if _scope_matches(item.owner_scope, scope)]

    def disable_rule(
        self,
        compatibility_rule_id: str,
        actor_id: str | None,
        reason: str,
    ) -> CompatibilityRule:
        get = getattr(self._repository, "get_rule", None)
        rule = get(compatibility_rule_id) if callable(get) else None
        if not isinstance(rule, CompatibilityRule):
            raise ValueError("compatibility_rule_not_found")
        authorize(
            self._policy_adapter,
            action_type="contract_registry.rule.update",
            resource_type="compatibility_rule",
            resource_id=compatibility_rule_id,
            scope=rule.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        updated = rule.model_copy(
            update={
                "status": "disabled",
                "updated_at": datetime.now(UTC),
                "disabled_at": datetime.now(UTC),
                "metadata": {**rule.metadata, "disable_reason": reason},
            }
        )
        save = getattr(self._repository, "save_rule", None)
        stored = save(updated) if callable(save) else updated
        return stored if isinstance(stored, CompatibilityRule) else updated

    def seed_default_rules(self, scope: list[str], dry_run: bool = True) -> dict[str, object]:
        rules = [default_rule(rule_type, scope) for rule_type in DEFAULT_RULE_TYPES]
        if dry_run:
            return {
                "dry_run": True,
                "rule_count": len(rules),
                "rule_types": [rule.rule_type for rule in rules],
            }
        created = [self.create_rule(rule) for rule in rules]
        return {
            "dry_run": False,
            "rule_count": len(created),
            "rule_ids": [rule.compatibility_rule_id for rule in created],
        }


def default_rule(rule_type: str, scope: list[str]) -> CompatibilityRule:
    severity = "high" if rule_type not in {"no_removed_cli_command"} else "medium"
    return CompatibilityRule(
        compatibility_rule_id=f"compat-rule-{rule_type}",
        name=rule_type,
        description=f"Generic compatibility rule: {rule_type}.",
        status="active",
        rule_type=cast(Any, rule_type),
        severity=cast(Any, severity),
        applies_to=["contract", "interface"],
        rule={"rule_type": rule_type, "source_mutation_allowed": False},
        owner_scope=scope,
        metadata={"default_rule": True},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


__all__ = ["CompatibilityRuleService", "DEFAULT_RULE_TYPES", "default_rule"]
