"""Transactional outbox service."""

from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.contracts.outbox import (
    OutboxMessage,
    OutboxProcessRequest,
    OutboxProcessResult,
    OutboxPublishRequest,
    OutboxStatus,
)
from aion_brain.contracts.telemetry import (
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.outbox.repository import OutboxRepository
from aion_brain.outbox.transports import (
    InternalOutboxTransport,
    NoopOutboxTransport,
    OutboxTransport,
    UnconfiguredNatsTransport,
    WebhookPlaceholderTransport,
)


class OutboxService:
    """Local transactional outbox with manual processing only."""

    def __init__(
        self,
        repository: OutboxRepository,
        *,
        settings: Settings,
        transports: dict[str, OutboxTransport] | None = None,
        telemetry_service: object | None = None,
        retry_policy_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._telemetry_service = telemetry_service
        self._retry_policy_service = retry_policy_service
        self._transports = transports or {
            "internal": InternalOutboxTransport(),
            "noop": NoopOutboxTransport(),
            "webhook_placeholder": WebhookPlaceholderTransport(),
            "nats": UnconfiguredNatsTransport(),
        }

    def set_retry_policy_service(self, retry_policy_service: object | None) -> None:
        """Attach retry policy metadata after kernel assembly."""
        self._retry_policy_service = retry_policy_service

    def enqueue(self, request: OutboxPublishRequest) -> OutboxMessage:
        """Enqueue one outbox message."""
        if not self._settings.outbox_enabled:
            raise PermissionError("outbox_disabled")
        now = datetime.now(UTC)
        message = OutboxMessage(
            outbox_id=f"outbox-{uuid4().hex}",
            trace_id=request.trace_id,
            correlation_id=request.correlation_id,
            message_type=request.message_type,
            destination=request.destination,
            subject=request.subject,
            payload=request.payload,
            headers=request.headers,
            status="pending",
            attempt_count=0,
            max_attempts=request.max_attempts,
            next_attempt_at=None,
            last_error={},
            created_at=now,
            sent_at=None,
            updated_at=now,
        )
        saved = self._repository.save(message)
        self._emit("outbox_message_enqueued", saved, 0.5)
        return saved

    def get(self, outbox_id: str) -> OutboxMessage | None:
        """Return one outbox message."""
        return self._repository.get(outbox_id)

    def list_messages(
        self,
        status: str | None = None,
        destination: str | None = None,
        limit: int = 50,
    ) -> list[OutboxMessage]:
        """List outbox messages."""
        return self._repository.list_messages(status=status, destination=destination, limit=limit)

    def process_once(self, request: OutboxProcessRequest) -> OutboxProcessResult:
        """Process pending messages once, manually and bounded."""
        messages = self._repository.list_messages(
            status="pending",
            destination=request.destination,
            limit=request.limit,
        )
        if request.dry_run:
            return OutboxProcessResult(
                processed=len(messages),
                sent=0,
                failed=0,
                skipped=len(messages),
                dry_run=True,
                messages=messages,
            )
        if not self._settings.outbox_process_enabled:
            raise PermissionError("outbox_process_disabled")

        sent = 0
        failed = 0
        skipped = 0
        processed_messages: list[OutboxMessage] = []
        for message in messages:
            updated = self._process_message(message)
            processed_messages.append(updated)
            if updated.status == "sent":
                sent += 1
            elif updated.status in {"failed", "dead_lettered"}:
                failed += 1
            else:
                skipped += 1
        return OutboxProcessResult(
            processed=len(processed_messages),
            sent=sent,
            failed=failed,
            skipped=skipped,
            dry_run=False,
            messages=processed_messages,
        )

    def cancel(self, outbox_id: str, reason: str | None = None) -> OutboxMessage:
        """Cancel one message without deleting it."""
        message = self._required(outbox_id)
        return self._repository.save(
            message.model_copy(
                update={
                    "status": "cancelled",
                    "last_error": {"reason": reason or "cancelled"},
                }
            )
        )

    def _process_message(self, message: OutboxMessage) -> OutboxMessage:
        attempt_number = message.attempt_count + 1
        transport = self._transports.get(message.destination)
        if transport is None:
            result_error: dict[str, object] = {"reason": "transport_unavailable"}
            return self._mark_failed(message, attempt_number, result_error)
        result = transport.send(message)
        if result.sent:
            saved = self._repository.save(
                message.model_copy(
                    update={
                        "status": "sent",
                        "attempt_count": attempt_number,
                        "sent_at": datetime.now(UTC),
                        "last_error": {},
                    }
                )
            )
            self._repository.save_attempt(
                delivery_attempt_id=f"delivery-attempt-{uuid4().hex}",
                outbox_id=saved.outbox_id,
                status="sent",
                attempt_number=attempt_number,
                error={},
                latency_ms=result.latency_ms,
            )
            self._emit("outbox_message_sent", saved, 0.8)
            return saved
        return self._mark_failed(message, attempt_number, result.error or {"reason": "send_failed"})

    def _mark_failed(
        self,
        message: OutboxMessage,
        attempt_number: int,
        error: dict[str, object],
    ) -> OutboxMessage:
        status: OutboxStatus = "failed"
        if attempt_number >= message.max_attempts:
            status = "dead_lettered"
        saved = self._repository.save(
            message.model_copy(
                update={
                    "status": status,
                    "attempt_count": attempt_number,
                    "last_error": dict(error),
                    "next_attempt_at": datetime.now(UTC)
                    + timedelta(milliseconds=self._retry_delay_ms(attempt_number)),
                }
            )
        )
        self._repository.save_attempt(
            delivery_attempt_id=f"delivery-attempt-{uuid4().hex}",
            outbox_id=saved.outbox_id,
            status=status,
            attempt_number=attempt_number,
            error=dict(error),
        )
        event_type = (
            "outbox_message_dead_lettered"
            if status == "dead_lettered"
            else "outbox_message_failed"
        )
        self._emit(event_type, saved, 1.0 if status == "dead_lettered" else 0.8)
        return saved

    def _retry_delay_ms(self, attempt_number: int) -> int:
        policy_for_target = getattr(self._retry_policy_service, "policy_for_target", None)
        compute_delay_ms = getattr(self._retry_policy_service, "compute_delay_ms", None)
        if callable(policy_for_target) and callable(compute_delay_ms):
            try:
                policy = policy_for_target("outbox")
                if policy is not None:
                    return int(compute_delay_ms(policy, attempt_number))
            except Exception:
                pass
        return 30000

    def _required(self, outbox_id: str) -> OutboxMessage:
        message = self._repository.get(outbox_id)
        if message is None:
            raise ValueError("outbox_message_not_found")
        return message

    def _emit(self, event_type: str, message: OutboxMessage, intensity: float) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{event_type}-{message.outbox_id}",
            trace_id=message.trace_id or message.outbox_id,
            event_type=cast(VisualTelemetryEventType, event_type),
            node_type="outbox",
            node_id=message.outbox_id,
            edge_from=message.trace_id,
            edge_to=message.outbox_id,
            intensity=intensity,
            payload={
                "destination": message.destination,
                "message_type": message.message_type,
            },
            created_at=datetime.now(UTC),
        )
        try:
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
        except Exception:
            return
