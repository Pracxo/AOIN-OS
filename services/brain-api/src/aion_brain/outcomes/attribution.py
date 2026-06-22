"""Causal attribution service."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.outcomes import CausalAttribution
from aion_brain.outcomes._shared import (
    audit_optional,
    authorize,
    emit_telemetry,
    provenance_optional,
)
from aion_brain.outcomes.repository import OutcomeRepository


class CausalAttributionService:
    """Manage generic causal attributions."""

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

    def create_attribution(self, attribution: CausalAttribution) -> CausalAttribution:
        """Create one attribution."""
        authorize(
            self._policy_adapter,
            action_type="outcome.attribution.create",
            resource_type="causal_attribution",
            resource_id=attribution.causal_attribution_id,
            scope=["workspace:main"],
            trace_id=attribution.trace_id,
            risk_level="low",
            context={"relation_type": attribution.relation_type},
        )
        stored = self._repository.save_attribution(
            attribution.model_copy(
                update={"created_at": attribution.created_at or datetime.now(UTC)}
            )
        )
        audit_optional(
            self._audit_sink,
            "causal_attribution_created",
            {"causal_attribution_id": stored.causal_attribution_id},
        )
        provenance_optional(
            self._provenance_service,
            stored.causal_attribution_id,
            stored.effect_id,
            stored.relation_type,
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="causal_attribution_created",
            node_type="causal_attribution",
            node_id=stored.causal_attribution_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            edge_from=stored.cause_id,
            edge_to=stored.effect_id,
            payload={"relation_type": stored.relation_type, "outcome_id": stored.outcome_id},
        )
        return stored

    def list_attributions(
        self,
        outcome_id: str | None = None,
        cause_type: str | None = None,
        cause_id: str | None = None,
        limit: int = 100,
    ) -> list[CausalAttribution]:
        """List attributions."""
        authorize(
            self._policy_adapter,
            action_type="outcome.attribution.read",
            resource_type="causal_attribution",
            resource_id=outcome_id or cause_id,
            scope=["workspace:main"],
        )
        return self._repository.list_attributions(
            outcome_id=outcome_id,
            cause_type=cause_type,
            cause_id=cause_id,
            limit=limit,
        )

    def soft_delete_attribution(
        self,
        causal_attribution_id: str,
        actor_id: str | None,
        reason: str,
    ) -> bool:
        """Soft delete an attribution."""
        authorize(
            self._policy_adapter,
            action_type="outcome.attribution.delete",
            resource_type="causal_attribution",
            resource_id=causal_attribution_id,
            scope=["workspace:main"],
            actor_id=actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        return self._repository.soft_delete_attribution(causal_attribution_id, reason)


__all__ = ["CausalAttributionService"]
