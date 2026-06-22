"""Event repository tests."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.events import AIONEvent
from aion_brain.events.repository import EventRepository


def make_repository() -> EventRepository:
    """Create an isolated repository backed by in-memory SQLite."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return EventRepository(engine=engine)


def make_event(event_id: str = "event-1", trace_id: str = "trace-1") -> AIONEvent:
    """Create a valid test event."""
    return AIONEvent(
        event_id=event_id,
        source="test-suite",
        event_type="test.received",
        actor_id="actor-1",
        workspace_id="workspace-1",
        payload_type="test.payload",
        payload={"message": "hello"},
        timestamp=datetime.now(UTC),
        correlation_id="corr-1",
        trace_id=trace_id,
        security_scope=["workspace:read"],
    )


def test_event_repository_persists_and_gets_event() -> None:
    """The event ledger stores and returns AIONEvent contracts."""
    repository = make_repository()
    event = make_event()

    saved = repository.save(event)
    loaded = repository.get(event.event_id)

    assert saved.event_id == event.event_id
    assert loaded is not None
    assert loaded.event_id == event.event_id
    assert loaded.payload == {"message": "hello"}
    assert loaded.security_scope == ["workspace:read"]


def test_event_repository_lists_events_by_trace() -> None:
    """The event ledger can list events by trace ID."""
    repository = make_repository()
    first = make_event(event_id="event-1", trace_id="trace-shared")
    second = make_event(event_id="event-2", trace_id="trace-shared").model_copy(
        update={"timestamp": first.timestamp + timedelta(seconds=1)}
    )
    other = make_event(event_id="event-3", trace_id="trace-other")

    repository.save(second)
    repository.save(other)
    repository.save(first)

    loaded = repository.list_by_trace("trace-shared")

    assert [event.event_id for event in loaded] == ["event-1", "event-2"]
