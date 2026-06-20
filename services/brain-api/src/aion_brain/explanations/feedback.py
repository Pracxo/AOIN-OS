"""Explanation feedback service."""

from __future__ import annotations

from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.contracts.explanations import ExplanationFeedback
from aion_brain.explanations._shared import authorize, emit_explanation_telemetry, now_utc
from aion_brain.explanations.repository import ExplanationRepository


class ExplanationFeedbackService:
    """Record and query feedback without mutating explanations."""

    def __init__(
        self,
        explanation_repository: ExplanationRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_ledger: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = explanation_repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_ledger = audit_ledger
        self._settings = settings

    def create_feedback(self, feedback: ExplanationFeedback) -> ExplanationFeedback:
        """Record feedback on an explanation, narrative, or why-not answer."""

        if not bool(getattr(self._settings, "explanation_feedback_enabled", True)):
            raise RuntimeError("explanation_feedback_disabled")
        target_id = feedback.explanation_id or feedback.trace_narrative_id or feedback.why_not_id
        authorize(
            self._policy_adapter,
            action_type="explanation.feedback.create",
            resource_type="explanation_feedback",
            resource_id=target_id,
            scope=_scope(feedback),
            actor_id=feedback.actor_id,
            context={"feedback_type": feedback.feedback_type},
        )
        stored = self._repository.save_feedback(
            feedback.model_copy(
                update={
                    "explanation_feedback_id": feedback.explanation_feedback_id
                    or f"explanation-feedback-{uuid4().hex}",
                    "created_at": feedback.created_at or now_utc(),
                }
            )
        )
        record_audit_event(
            self._audit_ledger,
            action_type="explanation.feedback.create",
            resource_type="explanation_feedback",
            resource_id=stored.explanation_feedback_id,
            event_type="explanation_feedback_recorded",
            outcome="completed",
            source_component="explanation_feedback_service",
            actor_id=stored.actor_id,
            payload={"feedback_type": stored.feedback_type, "rating": stored.rating},
            metadata={"owner_scope": _scope(stored)},
        )
        emit_explanation_telemetry(
            self._telemetry_service,
            event_type="explanation_feedback_recorded",
            node_type="explanation_feedback",
            node_id=stored.explanation_feedback_id,
            intensity=0.5,
            trace_id=None,
            owner_scope=_scope(stored),
            payload={"feedback_type": stored.feedback_type, "rating": stored.rating},
        )
        return stored

    def list_feedback(
        self,
        explanation_id: str | None = None,
        trace_narrative_id: str | None = None,
        why_not_id: str | None = None,
        limit: int = 100,
    ) -> list[ExplanationFeedback]:
        """List feedback records."""

        authorize(
            self._policy_adapter,
            action_type="explanation.feedback.read",
            resource_type="explanation_feedback",
            resource_id=explanation_id or trace_narrative_id or why_not_id,
            scope=["workspace:main"],
        )
        return self._repository.list_feedback(
            explanation_id=explanation_id,
            trace_narrative_id=trace_narrative_id,
            why_not_id=why_not_id,
            limit=limit,
        )


def _scope(feedback: ExplanationFeedback) -> list[str]:
    raw = feedback.metadata.get("owner_scope")
    if isinstance(raw, list) and raw:
        return [str(item) for item in raw]
    return ["workspace:main"]


__all__ = ["ExplanationFeedbackService"]
