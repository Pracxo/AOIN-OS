"""Outbox service tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.outbox import OutboxProcessRequest, OutboxPublishRequest
from aion_brain.outbox.repository import OutboxRepository
from aion_brain.outbox.service import OutboxService


def test_outbox_service_enqueues_message() -> None:
    """Outbox enqueue is a safe local write."""
    service = make_service()

    message = service.enqueue(publish_request())

    assert message.outbox_id.startswith("outbox-")
    assert message.status == "pending"


def test_outbox_process_once_dry_run_sends_nothing() -> None:
    """Dry-run process lists messages without sending."""
    service = make_service()
    service.enqueue(publish_request())

    result = service.process_once(OutboxProcessRequest(dry_run=True))

    assert result.processed == 1
    assert result.sent == 0
    assert result.skipped == 1


def test_outbox_process_once_non_dry_run_blocked_when_disabled() -> None:
    """Non-dry-run processing is blocked unless explicitly enabled."""
    service = make_service(outbox_process_enabled=False)
    service.enqueue(publish_request())

    with pytest.raises(PermissionError):
        service.process_once(OutboxProcessRequest(dry_run=False))


def test_outbox_internal_destination_marks_sent_when_enabled() -> None:
    """Internal destination marks sent when manual processing is enabled."""
    service = make_service(outbox_process_enabled=True)
    service.enqueue(publish_request(destination="internal"))

    result = service.process_once(OutboxProcessRequest(dry_run=False))

    assert result.sent == 1
    assert result.messages[0].status == "sent"


def test_outbox_webhook_placeholder_never_calls_network() -> None:
    """Webhook placeholder is failed locally."""
    service = make_service(outbox_process_enabled=True)
    service.enqueue(publish_request(destination="webhook_placeholder"))

    result = service.process_once(OutboxProcessRequest(dry_run=False))

    assert result.failed == 1
    assert result.messages[0].last_error["reason"] == "webhook_placeholder_disabled"


def make_service(*, outbox_process_enabled: bool = False) -> OutboxService:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        AION_OUTBOX_PROCESS_ENABLED=outbox_process_enabled,
    )
    return OutboxService(OutboxRepository(engine=engine), settings=settings)


def publish_request(destination: str = "noop") -> OutboxPublishRequest:
    return OutboxPublishRequest(
        message_type="event.publish",
        destination=destination,  # type: ignore[arg-type]
        subject="aion.events.generic",
        payload={"event_id": "event-1"},
    )
