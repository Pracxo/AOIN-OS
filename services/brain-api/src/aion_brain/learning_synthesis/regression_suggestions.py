"""Regression candidate suggestion service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.learning_synthesis import (
    LearningPattern,
    RegressionCandidateSuggestion,
)
from aion_brain.learning_synthesis.repository import LearningSynthesisRepository
from aion_brain.outcomes._shared import audit_optional, authorize, emit_telemetry


class RegressionSuggestionService:
    """Create reviewable regression suggestions without creating cases."""

    def __init__(
        self,
        repository: LearningSynthesisRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink

    def build_suggestion_from_failure(
        self,
        pattern: LearningPattern | None,
        outcome_id: str | None,
        created_by: str | None,
        owner_scope: list[str] | None = None,
    ) -> RegressionCandidateSuggestion:
        """Build but do not persist one regression suggestion."""
        scope = pattern.owner_scope if pattern else (owner_scope or ["workspace:main"])
        severity = pattern.severity if pattern else "medium"
        return RegressionCandidateSuggestion(
            regression_suggestion_id=f"regression-suggestion-{uuid4().hex}",
            trace_id=pattern.trace_id if pattern else None,
            pattern_id=pattern.pattern_id if pattern else None,
            outcome_id=outcome_id,
            status="suggested",
            title="Review regression coverage",
            description=(
                "A failure-like pattern may deserve regression coverage. "
                "This suggestion does not create a regression case."
            ),
            owner_scope=scope,
            source_refs=([pattern.pattern_id] if pattern else [])
            + ([outcome_id] if outcome_id else []),
            severity=severity,
            confidence=pattern.confidence if pattern else 0.6,
            metadata={"regression_case_created": False},
            created_by=created_by,
            created_at=datetime.now(UTC),
        )

    def create_suggestion_from_failure(
        self,
        pattern: LearningPattern | None,
        outcome_id: str | None,
        created_by: str | None,
    ) -> RegressionCandidateSuggestion:
        """Create one regression suggestion."""
        return self.create_suggestion(
            self.build_suggestion_from_failure(pattern, outcome_id, created_by)
        )

    def create_suggestion(
        self,
        suggestion: RegressionCandidateSuggestion,
    ) -> RegressionCandidateSuggestion:
        """Persist one regression suggestion."""
        authorize(
            self._policy_adapter,
            action_type="learning.regression_suggestion.create",
            resource_type="regression_suggestion",
            resource_id=suggestion.regression_suggestion_id,
            scope=suggestion.owner_scope,
            trace_id=suggestion.trace_id,
            risk_level="low",
            context={"regression_case_created": False},
        )
        stored = self._repository.save_regression_suggestion(
            suggestion.model_copy(update={"created_at": suggestion.created_at or datetime.now(UTC)})
        )
        audit_optional(
            self._audit_sink,
            "regression_candidate_suggestion_created",
            {"regression_suggestion_id": stored.regression_suggestion_id},
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="regression_candidate_suggestion_created",
            node_type="regression_suggestion",
            node_id=stored.regression_suggestion_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            payload={"severity": stored.severity},
        )
        return stored

    def list_suggestions(
        self,
        scope: list[str],
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[RegressionCandidateSuggestion]:
        """List regression suggestions in scope."""
        authorize(
            self._policy_adapter,
            action_type="learning.regression_suggestion.read",
            resource_type="regression_suggestion",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        return self._repository.list_regression_suggestions(
            scope,
            status=status,
            severity=severity,
            limit=limit,
        )

    def accept_suggestion(
        self,
        regression_suggestion_id: str,
        actor_id: str | None,
        reason: str,
    ) -> RegressionCandidateSuggestion:
        """Accept a suggestion without creating a regression case."""
        return self._update_status(regression_suggestion_id, "accepted", actor_id, reason)

    def reject_suggestion(
        self,
        regression_suggestion_id: str,
        actor_id: str | None,
        reason: str,
    ) -> RegressionCandidateSuggestion:
        """Reject a suggestion without creating a regression case."""
        return self._update_status(regression_suggestion_id, "rejected", actor_id, reason)

    def _update_status(
        self,
        regression_suggestion_id: str,
        status: str,
        actor_id: str | None,
        reason: str,
    ) -> RegressionCandidateSuggestion:
        suggestion = self._repository.get_regression_suggestion(regression_suggestion_id)
        if suggestion is None:
            raise ValueError("regression_suggestion_not_found")
        authorize(
            self._policy_adapter,
            action_type="learning.regression_suggestion.update",
            resource_type="regression_suggestion",
            resource_id=regression_suggestion_id,
            scope=suggestion.owner_scope,
            actor_id=actor_id,
            risk_level="low",
            context={"status": status, "reason": reason},
        )
        return self._repository.save_regression_suggestion(
            suggestion.model_copy(
                update={
                    "status": status,
                    "resolved_at": datetime.now(UTC),
                    "metadata": {
                        **suggestion.metadata,
                        "resolution_reason": reason,
                        "regression_case_created": False,
                    },
                }
            )
        )


__all__ = ["RegressionSuggestionService"]
