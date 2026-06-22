"""Deterministic clarification lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.dialogue import (
    ClarificationAnswerRequest,
    ClarificationRequest,
    DialogueMessageCreateRequest,
)
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.dialogue.message_service import DialogueMessageService
from aion_brain.dialogue.repository import DialogueRepository


class ClarificationManager:
    """Create, answer, cancel, and list clarification requests."""

    def __init__(
        self,
        repository: DialogueRepository,
        message_service: DialogueMessageService,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._message_service = message_service
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_clarification(
        self,
        dialogue_session_id: str | None,
        message_id: str | None,
        trace_id: str | None,
        question: str,
        reason: str,
        required: bool,
        metadata: dict[str, object],
    ) -> ClarificationRequest:
        """Create one pending clarification request."""

        scope = self._scope(dialogue_session_id)
        clarification_id = f"clarification-{uuid4().hex}"
        authorize(
            self._policy_adapter,
            action_type="dialogue.clarification.create",
            resource_type="clarification",
            resource_id=clarification_id,
            scope=scope,
            trace_id=trace_id,
            risk_level="low",
            context={"required": required},
        )
        clarification = ClarificationRequest(
            clarification_id=clarification_id,
            dialogue_session_id=dialogue_session_id,
            message_id=message_id,
            trace_id=trace_id,
            status="pending",
            question=question,
            reason=reason,
            required=required,
            answer_message_id=None,
            metadata=dict(metadata),
            created_at=datetime.now(UTC),
            answered_at=None,
            cancelled_at=None,
        )
        stored = self._repository.save_clarification(clarification)
        emit_telemetry(
            self._telemetry_service,
            event_type="clarification_requested",
            node_type="clarification",
            node_id=stored.clarification_id,
            intensity=0.8,
            trace_id=stored.trace_id,
            edge_from=stored.message_id,
            edge_to=stored.clarification_id,
            payload={"owner_scope": scope, "required": stored.required},
        )
        return stored

    def answer(self, request: ClarificationAnswerRequest) -> ClarificationRequest:
        """Record an answer as a normal dialogue message and mark answered."""

        clarification = self._require_clarification(request.clarification_id)
        scope = self._scope(clarification.dialogue_session_id)
        authorize(
            self._policy_adapter,
            action_type="dialogue.clarification.update",
            resource_type="clarification",
            resource_id=clarification.clarification_id,
            scope=scope,
            trace_id=clarification.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="low",
            context={"operation": "answer"},
        )
        answer_message_id: str | None = None
        if clarification.dialogue_session_id is not None:
            answer_message = self._message_service.create_message(
                DialogueMessageCreateRequest(
                    dialogue_session_id=clarification.dialogue_session_id,
                    trace_id=clarification.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    role="user",
                    message_type="clarification_answer",
                    content=request.answer,
                    metadata={
                        **request.metadata,
                        "clarification_id": clarification.clarification_id,
                    },
                )
            )
            answer_message_id = answer_message.message_id
        updated = clarification.model_copy(
            update={
                "status": "answered",
                "answer_message_id": answer_message_id,
                "answered_at": datetime.now(UTC),
                "metadata": {**clarification.metadata, "answer_metadata": request.metadata},
            }
        )
        stored = self._repository.save_clarification(updated)
        emit_telemetry(
            self._telemetry_service,
            event_type="clarification_answered",
            node_type="clarification",
            node_id=stored.clarification_id,
            intensity=0.6,
            trace_id=stored.trace_id,
            edge_from=stored.clarification_id,
            edge_to=stored.answer_message_id,
            payload={"owner_scope": scope},
        )
        return stored

    def cancel(
        self,
        clarification_id: str,
        actor_id: str | None,
        reason: str,
    ) -> ClarificationRequest:
        """Cancel a pending clarification."""

        clarification = self._require_clarification(clarification_id)
        scope = self._scope(clarification.dialogue_session_id)
        authorize(
            self._policy_adapter,
            action_type="dialogue.clarification.update",
            resource_type="clarification",
            resource_id=clarification_id,
            scope=scope,
            trace_id=clarification.trace_id,
            actor_id=actor_id,
            risk_level="low",
            context={"operation": "cancel", "reason": reason},
        )
        updated = clarification.model_copy(
            update={
                "status": "cancelled",
                "cancelled_at": datetime.now(UTC),
                "metadata": {
                    **clarification.metadata,
                    "cancelled_by": actor_id,
                    "cancel_reason": reason,
                },
            }
        )
        stored = self._repository.save_clarification(updated)
        emit_telemetry(
            self._telemetry_service,
            event_type="clarification_cancelled",
            node_type="clarification",
            node_id=stored.clarification_id,
            intensity=0.5,
            trace_id=stored.trace_id,
            payload={"owner_scope": scope, "reason": reason},
        )
        return stored

    def list_pending(
        self,
        scope: list[str],
        dialogue_session_id: str | None = None,
    ) -> list[ClarificationRequest]:
        """List pending clarification requests visible to a scope."""

        authorize(
            self._policy_adapter,
            action_type="dialogue.clarification.read",
            resource_type="clarification",
            resource_id=dialogue_session_id,
            scope=scope,
            context={"operation": "list_pending"},
        )
        pending = self._repository.list_pending_clarifications(
            dialogue_session_id=dialogue_session_id
        )
        return [
            item
            for item in pending
            if item.dialogue_session_id is None
            or _scope_matches(self._scope(item.dialogue_session_id), scope)
        ]

    def _require_clarification(self, clarification_id: str) -> ClarificationRequest:
        clarification = self._repository.get_clarification(clarification_id)
        if clarification is None:
            raise ValueError("clarification_not_found")
        return clarification

    def _scope(self, dialogue_session_id: str | None) -> list[str]:
        if dialogue_session_id is None:
            return ["workspace:main"]
        session = self._repository.get_session(dialogue_session_id)
        return session.owner_scope if session is not None else ["workspace:main"]


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope) & set(requested_scope))
