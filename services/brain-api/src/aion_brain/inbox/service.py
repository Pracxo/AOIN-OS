"""Inbox deduplication service."""

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.contracts.inbox import InboxMessage, InboxReceiveRequest, InboxReceiveResult
from aion_brain.contracts.telemetry import (
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.idempotency.hashing import sha256_json
from aion_brain.inbox.repository import InboxRepository


class InboxService:
    """Record incoming messages and suppress duplicate processing."""

    def __init__(self, repository: InboxRepository, *, telemetry_service: object | None = None):
        self._repository = repository
        self._telemetry_service = telemetry_service

    def receive(self, request: InboxReceiveRequest) -> InboxReceiveResult:
        """Record an incoming message without processing it automatically."""
        payload_hash = sha256_json(request.payload)
        existing = self._repository.get_by_external_id(
            request.source,
            request.external_message_id,
        )
        if existing is not None:
            if existing.payload_hash != payload_hash:
                failed = self._repository.save(
                    existing.model_copy(
                        update={
                            "status": "failed",
                            "error": {"reason": "inbox_payload_conflict"},
                        }
                    )
                )
                self._emit("inbox_duplicate_detected", failed, 0.7)
                return InboxReceiveResult(
                    accepted=False,
                    duplicate=True,
                    inbox=failed,
                    reason="inbox_payload_conflict",
                )
            duplicate = existing.model_copy(update={"status": "duplicate"})
            self._emit("inbox_duplicate_detected", duplicate, 0.6)
            return InboxReceiveResult(
                accepted=False,
                duplicate=True,
                inbox=duplicate,
                reason="duplicate_message",
            )
        message = InboxMessage(
            inbox_id=f"inbox-{uuid4().hex}",
            source=request.source,
            external_message_id=request.external_message_id,
            trace_id=request.trace_id,
            correlation_id=request.correlation_id,
            message_type=request.message_type,
            payload_hash=payload_hash,
            status="received",
            processed_by=None,
            result={},
            error={},
            received_at=datetime.now(UTC),
            processed_at=None,
        )
        saved = self._repository.save(message)
        self._emit("inbox_message_received", saved, 0.5)
        return InboxReceiveResult(accepted=True, duplicate=False, inbox=saved, reason=None)

    def mark_processed(
        self,
        inbox_id: str,
        processed_by: str,
        result: dict[str, object],
    ) -> InboxMessage:
        """Mark one inbox message as processed."""
        message = self._required(inbox_id)
        saved = self._repository.save(
            message.model_copy(
                update={
                    "status": "processed",
                    "processed_by": processed_by,
                    "result": dict(result),
                    "processed_at": datetime.now(UTC),
                }
            )
        )
        self._emit("inbox_message_processed", saved, 0.8)
        return saved

    def mark_failed(
        self,
        inbox_id: str,
        processed_by: str,
        error: dict[str, object],
    ) -> InboxMessage:
        """Mark one inbox message as failed."""
        message = self._required(inbox_id)
        saved = self._repository.save(
            message.model_copy(
                update={
                    "status": "failed",
                    "processed_by": processed_by,
                    "error": dict(error),
                    "processed_at": datetime.now(UTC),
                }
            )
        )
        self._emit("inbox_message_failed", saved, 0.9)
        return saved

    def list_messages(
        self,
        status: str | None = None,
        source: str | None = None,
        limit: int = 50,
    ) -> list[InboxMessage]:
        """List inbox messages."""
        return self._repository.list_messages(status=status, source=source, limit=limit)

    def _required(self, inbox_id: str) -> InboxMessage:
        message = self._repository.get(inbox_id)
        if message is None:
            raise ValueError("inbox_message_not_found")
        return message

    def _emit(self, event_type: str, message: InboxMessage, intensity: float) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{event_type}-{message.inbox_id}",
            trace_id=message.trace_id or message.inbox_id,
            event_type=cast(VisualTelemetryEventType, event_type),
            node_type="inbox",
            node_id=message.inbox_id,
            edge_from=None,
            edge_to=message.inbox_id,
            intensity=intensity,
            payload={"source": message.source, "message_type": message.message_type},
            created_at=datetime.now(UTC),
        )
        try:
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
        except Exception:
            return
