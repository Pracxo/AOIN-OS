"""Outcome feedback and learning bridge service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.outcomes import (
    OutcomeFeedback,
    OutcomeFeedbackSeverity,
    OutcomeFeedbackType,
)
from aion_brain.outcomes._shared import audit_optional, authorize, call_optional, emit_telemetry
from aion_brain.outcomes.repository import OutcomeRepository


class OutcomeFeedbackService:
    """Create feedback records without automatic remediation or skill promotion."""

    def __init__(
        self,
        repository: OutcomeRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        learning_engine: object | None = None,
        reflection_service: object | None = None,
        regression_service: object | None = None,
        skill_service: object | None = None,
        experience_service: object | None = None,
        learning_synthesizer: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._learning_engine = learning_engine
        self._reflection_service = reflection_service
        self._regression_service = regression_service
        self._skill_service = skill_service
        self._experience_service = experience_service
        self._learning_synthesizer = learning_synthesizer

    def create_feedback(self, feedback: OutcomeFeedback) -> OutcomeFeedback:
        """Create one feedback record."""
        authorize(
            self._policy_adapter,
            action_type="outcome.feedback.create",
            resource_type="outcome_feedback",
            resource_id=feedback.outcome_feedback_id,
            scope=["workspace:main"],
            trace_id=feedback.trace_id,
            risk_level=(
                feedback.severity if feedback.severity in {"low", "medium", "high"} else "high"
            ),
            context={"feedback_type": feedback.feedback_type, "no_skill_promotion": True},
        )
        stored = self._repository.save_feedback(
            feedback.model_copy(update={"created_at": feedback.created_at or datetime.now(UTC)})
        )
        audit_optional(
            self._audit_sink,
            "outcome_feedback_created",
            {
                "outcome_feedback_id": stored.outcome_feedback_id,
                "feedback_type": stored.feedback_type,
            },
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="outcome_feedback_created",
            node_type="outcome_feedback",
            node_id=stored.outcome_feedback_id,
            intensity=1.0 if stored.severity in {"high", "critical"} else 0.6,
            trace_id=stored.trace_id,
            payload={"outcome_id": stored.outcome_id, "severity": stored.severity},
        )
        return stored

    def list_feedback(
        self,
        outcome_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[OutcomeFeedback]:
        """List feedback records."""
        authorize(
            self._policy_adapter,
            action_type="outcome.feedback.read",
            resource_type="outcome_feedback",
            resource_id=outcome_id,
            scope=["workspace:main"],
        )
        return self._repository.list_feedback(
            outcome_id=outcome_id,
            status=status,
            severity=severity,
            limit=limit,
        )

    def resolve_feedback(
        self,
        outcome_feedback_id: str,
        actor_id: str | None,
        reason: str,
    ) -> OutcomeFeedback:
        """Resolve one feedback record."""
        feedback = self._repository.get_feedback(outcome_feedback_id)
        if feedback is None:
            raise ValueError("outcome_feedback_not_found")
        authorize(
            self._policy_adapter,
            action_type="outcome.feedback.update",
            resource_type="outcome_feedback",
            resource_id=outcome_feedback_id,
            scope=["workspace:main"],
            actor_id=actor_id,
            trace_id=feedback.trace_id,
            risk_level="low",
            context={"reason": reason},
        )
        updated = feedback.model_copy(
            update={
                "status": "resolved",
                "resolved_at": datetime.now(UTC),
                "metadata": {**feedback.metadata, "resolve_reason": reason},
            }
        )
        stored = self._repository.save_feedback(updated)
        emit_telemetry(
            self._telemetry_service,
            event_type="outcome_feedback_resolved",
            node_type="outcome_feedback",
            node_id=stored.outcome_feedback_id,
            intensity=0.4,
            trace_id=stored.trace_id,
            payload={"outcome_id": stored.outcome_id, "reason": reason},
        )
        return stored

    def bridge_to_learning(self, outcome_id: str, dry_run: bool = True) -> dict[str, object]:
        """Create learning bridge metadata; dry-run by default."""
        outcome = self._repository.get_outcome(outcome_id)
        if outcome is None:
            raise ValueError("outcome_not_found")
        authorize(
            self._policy_adapter,
            action_type="outcome.learning_bridge",
            resource_type="outcome",
            resource_id=outcome_id,
            scope=outcome.owner_scope,
            trace_id=outcome.trace_id,
            risk_level="medium" if not dry_run else "low",
            context={"dry_run": dry_run, "no_skill_promotion": True},
        )
        feedback_type = _feedback_type_for_outcome(outcome.status)
        feedback = OutcomeFeedback(
            outcome_feedback_id=f"outcome-feedback-{uuid4().hex}",
            trace_id=outcome.trace_id,
            outcome_id=outcome.outcome_id,
            source_type=outcome.source_type,
            source_id=outcome.source_id,
            feedback_type=feedback_type,
            status="open",
            severity=_severity_for_outcome(outcome.status),
            message=f"Outcome {outcome.status} recorded for {outcome.source_type}.",
            recommended_followup="Review outcome feedback before any learning or skill changes.",
            metadata={
                "dry_run": dry_run,
                "auto_skill_promotion": False,
                "auto_remediation": False,
            },
            created_by=outcome.created_by,
            created_at=datetime.now(UTC),
        )
        if dry_run:
            return {
                "dry_run": True,
                "would_create_feedback_type": feedback.feedback_type,
                "learning_signal_created": False,
                "experience_created": False,
                "skill_promoted": False,
            }
        stored = self.create_feedback(feedback)
        experience = call_optional(
            self._experience_service,
            ("create_from_outcome",),
            outcome_id,
            outcome.owner_scope,
        )
        learning_signal_id = call_optional(
            self._learning_engine,
            ("record", "record_signal", "create_learning_signal"),
            outcome_id=outcome_id,
            feedback_id=stored.outcome_feedback_id,
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="outcome_learning_feedback_created",
            node_type="outcome_feedback",
            node_id=stored.outcome_feedback_id,
            intensity=0.7,
            trace_id=stored.trace_id,
            payload={"outcome_id": outcome_id, "dry_run": False},
        )
        return {
            "dry_run": False,
            "feedback_id": stored.outcome_feedback_id,
            "experience_id": getattr(experience, "experience_id", None),
            "learning_signal_id": learning_signal_id,
            "skill_promoted": False,
            "reflection_created": False,
            "regression_case_created": False,
        }


def _feedback_type_for_outcome(status: str) -> OutcomeFeedbackType:
    if status == "verified":
        return "success_pattern"
    if status == "partial":
        return "partial_success"
    if status == "contradicted":
        return "contradiction"
    if status == "failed":
        return "failure_pattern"
    return "generic"


def _severity_for_outcome(status: str) -> OutcomeFeedbackSeverity:
    if status in {"failed", "contradicted"}:
        return "high"
    if status == "partial":
        return "medium"
    return "low"


__all__ = ["OutcomeFeedbackService"]
