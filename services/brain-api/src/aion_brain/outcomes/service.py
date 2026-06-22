"""Outcome record service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.effects import ExpectedEffect, ObservedEffect
from aion_brain.contracts.outcomes import (
    OutcomeCreateRequest,
    OutcomeQuery,
    OutcomeQueryResult,
    OutcomeRecord,
    OutcomeStatus,
)
from aion_brain.outcomes._shared import (
    audit_optional,
    authorize,
    clamp_score,
    emit_telemetry,
    provenance_optional,
    scope_matches,
)
from aion_brain.outcomes.repository import OutcomeRepository
from aion_brain.outcomes.verifier import compare_effects, score_comparison


class OutcomeService:
    """Create, query, close, and soft delete outcome records."""

    def __init__(
        self,
        repository: OutcomeRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings

    def create_outcome(self, request: OutcomeCreateRequest) -> OutcomeRecord:
        """Create one outcome record without mutating source records."""
        authorize(
            self._policy_adapter,
            action_type="outcome.create",
            resource_type="outcome",
            resource_id=request.outcome_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="low",
            context={"source_type": request.source_type, "outcome_type": request.outcome_type},
        )
        expected = self._load_expected(request.expected_effects)
        observed = self._load_observed(request.observed_effects)
        score, status = _initial_outcome_score_status(
            expected,
            observed,
            getattr(self._settings, "outcome_min_verified_score", 0.75),
        )
        if request.expected_effects and not expected:
            status = "unknown"
            score = request.score
        now = datetime.now(UTC)
        outcome = OutcomeRecord(
            outcome_id=request.outcome_id or f"outcome-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            source_type=request.source_type,
            source_id=request.source_id,
            status=status,
            outcome_type=request.outcome_type,
            title=request.title,
            summary=request.summary,
            owner_scope=request.owner_scope,
            expected_effects=request.expected_effects,
            observed_effects=request.observed_effects,
            evidence_refs=request.evidence_refs,
            memory_refs=request.memory_refs,
            belief_refs=request.belief_refs,
            situation_refs=request.situation_refs,
            decision_refs=request.decision_refs,
            execution_refs=request.execution_refs,
            confidence=request.confidence,
            score=clamp_score(score),
            metadata={**request.metadata, "source_mutated": False, "remediation_executed": False},
            observed_at=request.observed_at or now,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
        )
        stored = self._repository.save_outcome(outcome)
        audit_optional(
            self._audit_sink,
            "outcome_recorded",
            {"outcome_id": stored.outcome_id, "source_id": stored.source_id},
        )
        provenance_optional(
            self._provenance_service,
            stored.outcome_id,
            stored.source_id,
            "records_outcome_for",
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="outcome_recorded",
            node_type="outcome",
            node_id=stored.outcome_id,
            intensity=stored.score,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope, "status": stored.status},
        )
        return stored

    def get_outcome(self, outcome_id: str, scope: list[str]) -> OutcomeRecord | None:
        """Get one outcome if scope permits."""
        authorize(
            self._policy_adapter,
            action_type="outcome.read",
            resource_type="outcome",
            resource_id=outcome_id,
            scope=scope,
        )
        outcome = self._repository.get_outcome(outcome_id)
        if outcome is None or outcome.deleted_at is not None:
            return None
        if not scope_matches(outcome.owner_scope, scope):
            return None
        return outcome

    def query(self, query: OutcomeQuery) -> OutcomeQueryResult:
        """Query outcomes and related ledger records."""
        authorize(
            self._policy_adapter,
            action_type="outcome.read",
            resource_type="outcome",
            resource_id=None,
            scope=query.scope,
            trace_id=query.trace_id,
        )
        outcomes = self._repository.query_outcomes(query)
        expected_ids = {effect_id for outcome in outcomes for effect_id in outcome.expected_effects}
        observed_ids = {effect_id for outcome in outcomes for effect_id in outcome.observed_effects}
        expected = [
            expected_effect
            for effect_id in expected_ids
            if (expected_effect := self._repository.get_expected_effect(effect_id)) is not None
        ]
        observed = [
            observed_effect
            for effect_id in observed_ids
            if (observed_effect := self._repository.get_observed_effect(effect_id)) is not None
        ]
        verifications = [
            run
            for outcome in outcomes
            for run in self._repository.list_verification_runs(
                outcome_id=outcome.outcome_id,
                limit=25,
            )
        ]
        feedback = [
            item
            for outcome in outcomes
            for item in self._repository.list_feedback(outcome_id=outcome.outcome_id, limit=25)
        ]
        return OutcomeQueryResult(
            outcomes=outcomes,
            expected_effects=expected,
            observed_effects=observed,
            verifications=verifications,
            feedback=feedback,
            total_count=len(outcomes),
            metadata={"query": query.query, "include_deleted": query.include_deleted},
        )

    def close_outcome(
        self,
        outcome_id: str,
        actor_id: str | None,
        reason: str,
        scope: list[str] | None = None,
    ) -> OutcomeRecord:
        """Close an outcome by archiving it."""
        outcome = self._repository.get_outcome(outcome_id)
        if outcome is None:
            raise ValueError("outcome_not_found")
        authorize(
            self._policy_adapter,
            action_type="outcome.update",
            resource_type="outcome",
            resource_id=outcome_id,
            scope=scope or outcome.owner_scope,
            actor_id=actor_id,
            trace_id=outcome.trace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        now = datetime.now(UTC)
        closed = outcome.model_copy(
            update={
                "status": "archived",
                "closed_at": now,
                "updated_at": now,
                "metadata": {**outcome.metadata, "close_reason": reason},
            }
        )
        stored = self._repository.save_outcome(closed)
        emit_telemetry(
            self._telemetry_service,
            event_type="outcome_closed",
            node_type="outcome",
            node_id=stored.outcome_id,
            intensity=stored.score,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope, "reason": reason},
        )
        return stored

    def soft_delete_outcome(
        self,
        outcome_id: str,
        actor_id: str | None,
        reason: str,
        scope: list[str] | None = None,
    ) -> bool:
        """Soft delete an outcome."""
        outcome = self._repository.get_outcome(outcome_id)
        if outcome is None:
            return False
        authorize(
            self._policy_adapter,
            action_type="outcome.delete",
            resource_type="outcome",
            resource_id=outcome_id,
            scope=scope or outcome.owner_scope,
            actor_id=actor_id,
            trace_id=outcome.trace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        deleted = outcome.model_copy(
            update={
                "deleted_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "metadata": {**outcome.metadata, "delete_reason": reason},
            }
        )
        self._repository.save_outcome(deleted)
        return True

    def status(self, scope: list[str] | None = None) -> dict[str, object]:
        """Return compact status for operator cards."""
        outcomes = self._repository.list_outcomes(scope=scope or ["workspace:main"], limit=100)
        failed = len([item for item in outcomes if item.status in {"failed", "contradicted"}])
        return {
            "status": "failed" if failed else "healthy",
            "item_count": len(outcomes),
            "failed_count": failed,
        }

    def list_outcomes(
        self,
        scope: list[str],
        status: str | None = None,
        limit: int = 100,
    ) -> list[OutcomeRecord]:
        """List outcomes for operator integrations."""
        return self._repository.list_outcomes(scope=scope, status=status, limit=limit)

    def create_outcome_once_for_source(
        self,
        request: OutcomeCreateRequest,
    ) -> OutcomeRecord:
        """Create an outcome for a source only once."""
        existing = self._repository.get_outcome_by_source(request.source_type, request.source_id)
        if existing is not None:
            return existing
        return self.create_outcome(request)

    def _load_expected(self, ids: list[str]) -> list[ExpectedEffect]:
        return [
            effect
            for effect_id in ids
            if (effect := self._repository.get_expected_effect(effect_id)) is not None
        ]

    def _load_observed(self, ids: list[str]) -> list[ObservedEffect]:
        return [
            effect
            for effect_id in ids
            if (effect := self._repository.get_observed_effect(effect_id)) is not None
        ]


def _initial_outcome_score_status(
    expected: list[ExpectedEffect],
    observed: list[ObservedEffect],
    min_verified_score: float,
) -> tuple[float, OutcomeStatus]:
    if not expected:
        return 0.5, "unknown"
    comparison = compare_effects(expected, observed)
    score = score_comparison(expected, comparison)
    required_missing = [
        item for item in comparison["missing_effects"] if bool(item.get("required"))
    ]
    if comparison["contradicted_effects"]:
        return score, "contradicted"
    if required_missing and not comparison["matched_effects"]:
        return score, "failed"
    if required_missing or comparison["missing_effects"] or comparison["unexpected_effects"]:
        return score, "partial"
    if score >= min_verified_score:
        return max(score, min_verified_score), "verified"
    return score, "unknown"


__all__ = ["OutcomeService"]
