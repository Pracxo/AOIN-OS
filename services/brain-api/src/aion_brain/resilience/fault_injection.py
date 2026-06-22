"""Local fault injection harness."""

from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import Any, cast

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.resilience import FaultInjectionRule
from aion_brain.policy.base import PolicyAdapter
from aion_brain.resilience._shared import authorize, emit_resilience_event
from aion_brain.resilience.repository import ResilienceRepository


class FaultInjectionService:
    """Manage local deterministic fault injection rules."""

    def __init__(
        self,
        repository: ResilienceRepository,
        policy_adapter: PolicyAdapter,
        *,
        settings: Settings | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._settings = settings or get_settings()
        self._telemetry_service = telemetry_service

    def create_rule(self, rule: FaultInjectionRule) -> FaultInjectionRule:
        """Create or replace one fault rule."""
        authorize(
            self._policy_adapter,
            "resilience.fault_rule.create",
            rule.owner_scope,
            actor_id=rule.created_by,
            resource_type="fault_rule",
            resource_id=rule.fault_rule_id,
            risk_level="medium",
            context={"env": self._settings.env},
        )
        now = datetime.now(UTC)
        saved = self._repository.save_fault_rule(
            rule.model_copy(
                update={
                    "created_at": rule.created_at or now,
                    "updated_at": now,
                }
            )
        )
        emit_resilience_event(
            self._telemetry_service,
            event_type="fault_rule_created",
            node_type="fault_rule",
            node_id=saved.fault_rule_id,
            intensity=0.6,
            payload={"target_type": saved.target_type, "fault_type": saved.fault_type},
        )
        return saved

    def list_rules(
        self,
        status: str | None = None,
        target_type: str | None = None,
    ) -> list[FaultInjectionRule]:
        """List fault rules."""
        authorize(
            self._policy_adapter,
            "resilience.fault_rule.read",
            ["workspace:main"],
            context={"status": status, "target_type": target_type},
        )
        return self._repository.list_fault_rules(status=status, target_type=target_type)

    def disable_rule(
        self,
        fault_rule_id: str,
        actor_id: str | None,
        reason: str,
    ) -> FaultInjectionRule:
        """Disable one fault rule."""
        authorize(
            self._policy_adapter,
            "resilience.fault_rule.update",
            ["workspace:main"],
            actor_id=actor_id,
            resource_type="fault_rule",
            resource_id=fault_rule_id,
            risk_level="medium",
            context={"reason": reason, "env": self._settings.env},
        )
        rule = self._repository.get_fault_rule(fault_rule_id)
        if rule is None:
            raise AIONNotFoundException("fault_rule_not_found")
        return self._repository.save_fault_rule(
            rule.model_copy(
                update={
                    "status": cast(Any, "disabled"),
                    "disabled_at": datetime.now(UTC),
                    "metadata": {**rule.metadata, "disable_reason": reason},
                }
            )
        )

    def should_inject(
        self,
        target_type: str,
        target_id: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> FaultInjectionRule | None:
        """Return a matching active fault rule when deterministic probability allows it."""
        if not self._settings.fault_injection_enabled:
            return None
        meta = metadata or {}
        for rule in self._repository.list_fault_rules(status="active", target_type=target_type):
            if rule.target_id is not None and target_id is not None and rule.target_id != target_id:
                continue
            if rule.target_id is not None and target_id is None:
                continue
            seed = meta.get("seed", rule.metadata.get("seed", f"{rule.fault_rule_id}:{target_id}"))
            rng = random.Random(str(seed))
            if rng.random() <= rule.probability:
                return rule
        return None

    def apply_fault(self, rule: FaultInjectionRule) -> dict[str, Any]:
        """Return the fault outcome without external side effects."""
        result = {
            "fault_rule_id": rule.fault_rule_id,
            "fault_type": rule.fault_type,
            "target_type": rule.target_type,
            "target_id": rule.target_id,
            "error_code": rule.error_code,
            "duration_ms": rule.duration_ms,
            "would_inject": bool(self._settings.fault_injection_enabled),
        }
        emit_resilience_event(
            self._telemetry_service,
            event_type="fault_injected",
            node_type="fault_rule",
            node_id=rule.fault_rule_id,
            intensity=0.9,
            payload=result,
        )
        return result
