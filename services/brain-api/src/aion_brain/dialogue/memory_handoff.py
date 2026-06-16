"""Explicit dialogue-to-memory handoff."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.memory import MemoryRecord
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.dialogue.redaction import redact_message_content
from aion_brain.dialogue.repository import DialogueRepository


class DialogueMemoryHandoffService:
    """Create governed memory records from sanitized dialogue summaries."""

    def __init__(
        self,
        repository: DialogueRepository,
        policy_adapter: object,
        memory_service: object | None,
        *,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._memory_service = memory_service
        self._telemetry_service = telemetry_service
        self._settings = settings

    def propose_memory_from_message(self, message_id: str, scope: list[str]) -> dict[str, object]:
        """Return a deterministic memory proposal without writing memory."""

        message = self._repository.get_message(message_id)
        if message is None or message.deleted_at is not None:
            raise ValueError("dialogue_message_not_found")
        authorize(
            self._policy_adapter,
            action_type="dialogue.memory_handoff",
            resource_type="dialogue_message",
            resource_id=message_id,
            scope=scope,
            trace_id=message.trace_id,
            risk_level="medium",
            context={"operation": "propose"},
        )
        sanitized, _ = redact_message_content(message.content)
        return {
            "message_id": message.message_id,
            "memory_type": "episodic",
            "summary": sanitized[:500],
            "evidence_refs": message.evidence_refs,
            "memory_refs": message.memory_refs,
            "owner_scope": scope,
        }

    def remember_message_summary(
        self,
        message_id: str,
        scope: list[str],
        approval_present: bool = False,
    ) -> dict[str, object]:
        """Write a governed memory summary only when metadata.remember=true."""

        message = self._repository.get_message(message_id)
        if message is None or message.deleted_at is not None:
            raise ValueError("dialogue_message_not_found")
        if message.metadata.get("remember") is not True:
            return {"remembered": False, "message_id": message_id, "reason": "not_requested"}
        if not bool(getattr(self._settings, "dialogue_memory_handoff_enabled", True)):
            return {"remembered": False, "message_id": message_id, "reason": "handoff_disabled"}
        authorize(
            self._policy_adapter,
            action_type="dialogue.memory_handoff",
            resource_type="dialogue_message",
            resource_id=message_id,
            scope=scope,
            trace_id=message.trace_id,
            actor_id=message.actor_id,
            workspace_id=message.workspace_id,
            risk_level="medium",
            approval_present=approval_present,
            context={"operation": "remember"},
        )
        create = getattr(self._memory_service, "create", None)
        if not callable(create):
            return {"remembered": False, "message_id": message_id, "reason": "memory_unavailable"}
        proposal = self.propose_memory_from_message(message_id, scope)
        memory = MemoryRecord(
            memory_id=f"dialogue-memory-{uuid4().hex}",
            memory_type="episodic",
            owner_scope=scope,
            source_event_id=None,
            content_ref=f"dialogue_message:{message_id}",
            summary=str(proposal["summary"]),
            confidence=0.7,
            sensitivity="low",
            created_at=datetime.now(UTC),
            expires_at=None,
            metadata={
                "dialogue_session_id": message.dialogue_session_id,
                "message_id": message.message_id,
                "trace_id": message.trace_id,
                "evidence_refs": message.evidence_refs,
                "recall_only": True,
            },
        )
        stored = create(memory)
        memory_id = getattr(stored, "memory_id", memory.memory_id)
        emit_telemetry(
            self._telemetry_service,
            event_type="dialogue_memory_handoff_created",
            node_type="memory",
            node_id=str(memory_id),
            intensity=0.6,
            trace_id=message.trace_id,
            edge_from=message.message_id,
            edge_to=str(memory_id),
            payload={"owner_scope": scope, "dialogue_session_id": message.dialogue_session_id},
        )
        return {"remembered": True, "message_id": message_id, "memory_id": str(memory_id)}
