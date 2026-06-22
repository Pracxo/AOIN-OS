"""Inbox service tests."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.inbox import InboxReceiveRequest
from aion_brain.inbox.repository import InboxRepository
from aion_brain.inbox.service import InboxService


def test_inbox_service_accepts_new_message() -> None:
    """A new external message is accepted."""
    result = make_service().receive(request())

    assert result.accepted is True
    assert result.duplicate is False


def test_inbox_service_detects_duplicate_message() -> None:
    """Same source and message id with same payload is duplicate."""
    service = make_service()
    service.receive(request())

    result = service.receive(request())

    assert result.duplicate is True
    assert result.reason == "duplicate_message"


def test_inbox_service_detects_payload_conflict() -> None:
    """Same source and message id with different payload conflicts."""
    service = make_service()
    service.receive(request())

    result = service.receive(request(payload={"value": 2}))

    assert result.duplicate is True
    assert result.reason == "inbox_payload_conflict"
    assert result.inbox.status == "failed"


def make_service() -> InboxService:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return InboxService(InboxRepository(engine=engine))


def request(payload: dict[str, object] | None = None) -> InboxReceiveRequest:
    return InboxReceiveRequest(
        source="nats",
        external_message_id="message-1",
        message_type="event",
        payload=payload or {"value": 1},
    )
