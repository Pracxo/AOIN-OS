"""Dialogue message store."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.dialogue import DialogueMessage, DialogueMessageCreateRequest
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.dialogue.hashing import hash_message_content
from aion_brain.dialogue.redaction import redact_message_content
from aion_brain.dialogue.repository import DialogueRepository


class DialogueMessageService:
    """Create, read, list, and soft-delete sanitized dialogue messages."""

    def __init__(
        self,
        repository: DialogueRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings

    def create_message(self, request: DialogueMessageCreateRequest) -> DialogueMessage:
        """Redact, hash, authorize, and store one dialogue message."""

        session = self._repository.get_session(request.dialogue_session_id)
        scope = session.owner_scope if session is not None else ["workspace:main"]
        message_id = request.message_id or f"dialogue-message-{uuid4().hex}"
        authorize(
            self._policy_adapter,
            action_type="dialogue.message.create",
            resource_type="dialogue_message",
            resource_id=message_id,
            scope=scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="low",
            context={"role": request.role, "message_type": request.message_type},
        )
        content, content_redacted = _sanitize(request.content, self._settings)
        now = datetime.now(UTC)
        message = DialogueMessage(
            message_id=message_id,
            dialogue_session_id=request.dialogue_session_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            role=request.role,
            message_type=request.message_type,
            content=content,
            content_hash=hash_message_content(content),
            content_redacted=content_redacted,
            grounding_refs=request.grounding_refs,
            memory_refs=request.memory_refs,
            evidence_refs=request.evidence_refs,
            response_refs=[],
            metadata=request.metadata,
            created_at=now,
            deleted_at=None,
        )
        if bool(getattr(self._settings, "dialogue_store_messages", True)):
            stored = self._repository.save_message(message)
        else:
            stored = message
        emit_telemetry(
            self._telemetry_service,
            event_type="dialogue_message_created",
            node_type="message",
            node_id=stored.message_id,
            intensity=0.4,
            trace_id=stored.trace_id,
            edge_from=stored.dialogue_session_id,
            edge_to=stored.message_id,
            payload={
                "owner_scope": scope,
                "workspace_id": stored.workspace_id,
                "role": stored.role,
                "message_type": stored.message_type,
            },
        )
        return stored

    def get_message(self, message_id: str, scope: list[str]) -> DialogueMessage | None:
        """Return one visible non-deleted message."""

        authorize(
            self._policy_adapter,
            action_type="dialogue.message.read",
            resource_type="dialogue_message",
            resource_id=message_id,
            scope=scope,
            context={},
        )
        message = self._repository.get_message(message_id)
        if message is None or message.deleted_at is not None:
            return None
        session = self._repository.get_session(message.dialogue_session_id)
        if session is not None and not _scope_matches(session.owner_scope, scope):
            return None
        return message

    def list_messages(
        self,
        dialogue_session_id: str,
        scope: list[str],
        limit: int = 100,
    ) -> list[DialogueMessage]:
        """List visible non-deleted messages in creation order."""

        authorize(
            self._policy_adapter,
            action_type="dialogue.message.read",
            resource_type="dialogue_message",
            resource_id=dialogue_session_id,
            scope=scope,
            context={"operation": "list_messages"},
        )
        session = self._repository.get_session(dialogue_session_id)
        if session is None or not _scope_matches(session.owner_scope, scope):
            return []
        return self._repository.list_messages(dialogue_session_id, limit=limit)

    def soft_delete_message(
        self,
        message_id: str,
        actor_id: str | None,
        reason: str,
    ) -> bool:
        """Soft delete a message."""

        message = self._repository.get_message(message_id)
        if message is None:
            return False
        session = self._repository.get_session(message.dialogue_session_id)
        scope = session.owner_scope if session is not None else ["workspace:main"]
        authorize(
            self._policy_adapter,
            action_type="dialogue.message.delete",
            resource_type="dialogue_message",
            resource_id=message_id,
            scope=scope,
            trace_id=message.trace_id,
            actor_id=actor_id,
            workspace_id=message.workspace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        deleted = self._repository.soft_delete_message(message_id, datetime.now(UTC))
        if deleted:
            emit_telemetry(
                self._telemetry_service,
                event_type="dialogue_message_deleted",
                node_type="message",
                node_id=message_id,
                intensity=0.4,
                trace_id=message.trace_id,
                payload={"owner_scope": scope, "reason": reason},
            )
        return deleted


def _sanitize(content: str, settings: object | None) -> tuple[str, bool]:
    if bool(getattr(settings, "dialogue_redact_sensitive_content", True)):
        return redact_message_content(content)
    return content.strip(), False


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope) & set(requested_scope))
