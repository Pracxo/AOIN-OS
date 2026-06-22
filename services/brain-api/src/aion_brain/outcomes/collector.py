"""Observed effect collection from local AION records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.contracts.effects import (
    EffectSourceType,
    EffectType,
    ObservationSourceType,
    ObservedEffect,
    ObservedEffectCreateRequest,
)
from aion_brain.outcomes._shared import authorize, emit_telemetry
from aion_brain.outcomes.repository import OutcomeRepository

_SOURCE_EFFECTS: dict[str, tuple[str, str, str]] = {
    "command": ("command_completed", "status", "command"),
    "workflow": ("workflow_completed", "status", "workflow"),
    "response": ("response_delivered", "status", "response"),
    "evidence": ("evidence_created", "status", "evidence"),
    "memory": ("memory_written", "status", "memory"),
    "approval": ("approval_requested", "status", "operator"),
    "situation": ("state_change", "state", "situation"),
    "state_atom": ("state_change", "state", "state_atom"),
    "belief_claim": ("status_change", "status", "belief_claim"),
}


class ObservedEffectCollector:
    """Record and collect generic observed effects from local sources."""

    def __init__(
        self,
        repository: OutcomeRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_observed_effect(self, request: ObservedEffectCreateRequest) -> ObservedEffect:
        """Create one observed effect."""
        authorize(
            self._policy_adapter,
            action_type="outcome.observed_effect.create",
            resource_type="observed_effect",
            resource_id=request.observed_effect_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            risk_level="low",
            context={"source_type": request.source_type, "effect_type": request.effect_type},
        )
        effect = ObservedEffect(
            observed_effect_id=request.observed_effect_id or f"observed-effect-{uuid4().hex}",
            trace_id=request.trace_id,
            outcome_id=request.outcome_id,
            source_type=request.source_type,
            source_id=request.source_id,
            effect_type=request.effect_type,
            subject_ref=request.subject_ref,
            predicate=request.predicate,
            object_ref=request.object_ref,
            observed_value=request.observed_value,
            observation_source_type=request.observation_source_type,
            observation_source_id=request.observation_source_id,
            confidence=request.confidence,
            sensitivity=request.sensitivity,
            owner_scope=request.owner_scope,
            evidence_refs=request.evidence_refs,
            belief_refs=request.belief_refs,
            situation_refs=request.situation_refs,
            metadata=request.metadata,
            observed_at=request.observed_at or datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_observed_effect(effect)
        emit_telemetry(
            self._telemetry_service,
            event_type="observed_effect_recorded",
            node_type="observed_effect",
            node_id=stored.observed_effect_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope, "effect_type": stored.effect_type},
        )
        return stored

    def collect_for_source(
        self,
        source_type: str,
        source_id: str,
        scope: list[str],
        trace_id: str | None = None,
    ) -> list[ObservedEffect]:
        """Collect a deterministic observed effect for a known local source type."""
        existing = self._repository.list_observed_effects(
            source_type=source_type,
            source_id=source_id,
            trace_id=trace_id,
            limit=10,
        )
        if existing:
            return existing
        effect_type, predicate, observation_source_type = _SOURCE_EFFECTS.get(
            source_type,
            ("generic", "status", "generic"),
        )
        effect = self.create_observed_effect(
            ObservedEffectCreateRequest(
                trace_id=trace_id,
                source_type=cast(EffectSourceType, _source_type(source_type)),
                source_id=source_id,
                effect_type=cast(EffectType, effect_type),
                predicate=predicate,
                observed_value={"status": _observed_status(source_type)},
                observation_source_type=cast(ObservationSourceType, observation_source_type),
                observation_source_id=source_id,
                confidence=0.8 if source_type in _SOURCE_EFFECTS else 0.5,
                owner_scope=scope,
                metadata={"collected": True, "source_type": source_type},
            )
        )
        return [effect]

    def list_observed_effects(
        self,
        outcome_id: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        limit: int = 100,
    ) -> list[ObservedEffect]:
        """List observed effects after read authorization."""
        authorize(
            self._policy_adapter,
            action_type="outcome.observed_effect.read",
            resource_type="observed_effect",
            resource_id=outcome_id or source_id,
            scope=["workspace:main"],
        )
        return self._repository.list_observed_effects(
            outcome_id=outcome_id,
            source_type=source_type,
            source_id=source_id,
            limit=limit,
        )


def _source_type(source_type: str) -> str:
    if source_type in {
        "decision_option",
        "decision_record",
        "counterfactual",
        "plan",
        "execution",
        "workflow",
        "task",
        "command",
        "event_reaction",
        "cycle",
    }:
        return source_type
    return "generic"


def _observed_status(source_type: str) -> str:
    if source_type in {"command", "workflow", "response", "evidence", "memory"}:
        return "completed"
    if source_type == "approval":
        return "requested"
    if source_type in {"situation", "state_atom"}:
        return "changed"
    return "observed"


__all__ = ["ObservedEffectCollector"]
