"""Expected effect service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.effects import ExpectedEffect, ExpectedEffectCreateRequest
from aion_brain.outcomes._shared import (
    audit_optional,
    authorize,
    emit_telemetry,
    provenance_optional,
)
from aion_brain.outcomes.repository import OutcomeRepository


class ExpectedEffectService:
    """Manage expected effects behind the outcome policy boundary."""

    def __init__(
        self,
        repository: OutcomeRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service

    def create_expected_effect(self, request: ExpectedEffectCreateRequest) -> ExpectedEffect:
        """Create one expected effect."""
        authorize(
            self._policy_adapter,
            action_type="outcome.expected_effect.create",
            resource_type="expected_effect",
            resource_id=request.expected_effect_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            risk_level="low",
            context={"source_type": request.source_type, "effect_type": request.effect_type},
        )
        effect = ExpectedEffect(
            expected_effect_id=request.expected_effect_id or f"expected-effect-{uuid4().hex}",
            trace_id=request.trace_id,
            source_type=request.source_type,
            source_id=request.source_id,
            effect_type=request.effect_type,
            subject_ref=request.subject_ref,
            predicate=request.predicate,
            object_ref=request.object_ref,
            expected_value=request.expected_value,
            success_criteria=request.success_criteria,
            required=request.required,
            confidence=request.confidence,
            owner_scope=request.owner_scope,
            evidence_refs=request.evidence_refs,
            metadata=request.metadata,
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_expected_effect(effect)
        audit_optional(
            self._audit_sink,
            "expected_effect_created",
            {"expected_effect_id": stored.expected_effect_id, "source_id": stored.source_id},
        )
        provenance_optional(
            self._provenance_service,
            stored.expected_effect_id,
            stored.source_id,
            "expects_effect_from",
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="expected_effect_created",
            node_type="expected_effect",
            node_id=stored.expected_effect_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope, "effect_type": stored.effect_type},
        )
        return stored

    def list_expected_effects(
        self,
        source_type: str | None = None,
        source_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> list[ExpectedEffect]:
        """List expected effects after read authorization."""
        authorize(
            self._policy_adapter,
            action_type="outcome.expected_effect.read",
            resource_type="expected_effect",
            resource_id=source_id,
            scope=["workspace:main"],
            trace_id=trace_id,
        )
        return self._repository.list_expected_effects(
            source_type=source_type,
            source_id=source_id,
            trace_id=trace_id,
            limit=limit,
        )

    def soft_delete_expected_effect(
        self,
        expected_effect_id: str,
        actor_id: str | None,
        reason: str,
    ) -> bool:
        """Soft delete one expected effect."""
        effect = self._repository.get_expected_effect(expected_effect_id)
        if effect is None:
            return False
        authorize(
            self._policy_adapter,
            action_type="outcome.expected_effect.delete",
            resource_type="expected_effect",
            resource_id=expected_effect_id,
            scope=effect.owner_scope,
            actor_id=actor_id,
            trace_id=effect.trace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        return self._repository.soft_delete_expected_effect(expected_effect_id, reason)


__all__ = ["ExpectedEffectService"]
