"""Dialogue feedback records."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.dialogue import DialogueFeedback
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.dialogue.repository import DialogueRepository


class DialogueFeedbackService:
    """Create and list local dialogue feedback records."""

    def __init__(
        self,
        repository: DialogueRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_feedback(self, feedback: DialogueFeedback) -> DialogueFeedback:
        """Create feedback after policy authorization."""

        scope = _scope_from_feedback(feedback)
        authorize(
            self._policy_adapter,
            action_type="dialogue.feedback.create",
            resource_type="dialogue_feedback",
            resource_id=feedback.feedback_id,
            scope=scope,
            trace_id=feedback.trace_id,
            actor_id=feedback.actor_id,
            risk_level="low",
            context={"feedback_type": feedback.feedback_type},
        )
        stored = self._repository.save_feedback(
            feedback.model_copy(update={"created_at": feedback.created_at or datetime.now(UTC)})
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="dialogue_feedback_recorded",
            node_type="feedback",
            node_id=stored.feedback_id,
            intensity=0.4,
            trace_id=stored.trace_id,
            edge_from=stored.response_id or stored.message_id,
            edge_to=stored.feedback_id,
            payload={"owner_scope": scope, "feedback_type": stored.feedback_type},
        )
        return stored

    def list_feedback(
        self,
        dialogue_session_id: str | None = None,
        response_id: str | None = None,
        limit: int = 100,
    ) -> list[DialogueFeedback]:
        """List local feedback records."""

        authorize(
            self._policy_adapter,
            action_type="dialogue.feedback.read",
            resource_type="dialogue_feedback",
            resource_id=response_id or dialogue_session_id,
            scope=["workspace:main"],
            context={"operation": "list_feedback"},
        )
        return self._repository.list_feedback(
            dialogue_session_id=dialogue_session_id,
            response_id=response_id,
            limit=limit,
        )


def _scope_from_feedback(feedback: DialogueFeedback) -> list[str]:
    raw = feedback.metadata.get("owner_scope") or feedback.metadata.get("scope")
    if isinstance(raw, list):
        values = [str(item) for item in raw]
        if values:
            return values
    return ["workspace:main"]
