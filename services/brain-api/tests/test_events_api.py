"""Event intake API tests."""

from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from aion_brain.api.events import (
    get_event_publisher,
    get_event_reaction_router_for_intake,
    get_event_repository,
)
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.event_reactions import EventDispatchRequest
from aion_brain.contracts.events import AIONEvent
from aion_brain.events.publisher import NoopEventPublisher
from aion_brain.main import app


class FakeEventRepository:
    """In-memory repository fake for event API tests."""

    def __init__(self) -> None:
        self.events: list[AIONEvent] = []

    def save(self, event: AIONEvent) -> AIONEvent:
        self.events.append(event)
        return event


class FakeEventReactionRouter:
    """Fake event reaction router for intake integration tests."""

    def __init__(self) -> None:
        self.requests: list[EventDispatchRequest] = []

    def dispatch(self, request: EventDispatchRequest) -> object:
        self.requests.append(request)
        return {"dispatch_id": "dispatch-1"}


@pytest.fixture
def fake_repository() -> FakeEventRepository:
    """Create a fake event repository."""
    return FakeEventRepository()


@pytest.fixture
def fake_publisher() -> NoopEventPublisher:
    """Create a fake event publisher."""
    return NoopEventPublisher()


@pytest.fixture
def client(
    fake_repository: FakeEventRepository,
    fake_publisher: NoopEventPublisher,
) -> TestClient:
    """Create a test client with event dependencies overridden."""
    app.dependency_overrides[get_event_repository] = lambda: fake_repository
    app.dependency_overrides[get_event_publisher] = lambda: fake_publisher
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def valid_event_payload() -> dict[str, Any]:
    """Return a valid event request payload."""
    return {
        "event_id": "event-1",
        "source": "test-suite",
        "event_type": "test.received",
        "actor_id": "actor-1",
        "workspace_id": "workspace-1",
        "payload_type": "test.payload",
        "payload": {"message": "hello"},
        "timestamp": datetime.now(UTC).isoformat(),
        "security_scope": ["workspace:read"],
    }


def test_post_brain_events_accepts_valid_event(
    client: TestClient,
    fake_repository: FakeEventRepository,
    fake_publisher: NoopEventPublisher,
) -> None:
    """POST /brain/events accepts, persists, and publishes a valid event."""
    response = client.post("/brain/events", json=valid_event_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert body["event_id"] == "event-1"
    assert body["trace_id"].startswith("trace-")
    assert body["correlation_id"].startswith("corr-")
    assert body["persisted"] is True
    assert body["published"] is True
    assert fake_repository.events[0].trace_id == body["trace_id"]
    assert fake_publisher.events[0].event_id == "event-1"


def test_post_brain_events_rejects_missing_required_fields(client: TestClient) -> None:
    """Missing required event fields return a validation error."""
    payload = valid_event_payload()
    del payload["source"]

    response = client.post("/brain/events", json=payload)

    assert response.status_code == 422


def test_post_brain_events_returns_published_false_when_publisher_fails(
    fake_repository: FakeEventRepository,
) -> None:
    """Publishing failure does not erase the persisted event."""
    failing_publisher = NoopEventPublisher(published=False)
    app.dependency_overrides[get_event_repository] = lambda: fake_repository
    app.dependency_overrides[get_event_publisher] = lambda: failing_publisher
    try:
        response = TestClient(app).post("/brain/events", json=valid_event_payload())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["published"] is False
    assert response.json()["persisted"] is True
    assert len(fake_repository.events) == 1
    assert len(failing_publisher.events) == 1


def test_post_brain_events_preserves_existing_trace_and_correlation_ids(
    client: TestClient,
) -> None:
    """The intake engine preserves caller-provided trace and correlation IDs."""
    payload = valid_event_payload()
    payload["trace_id"] = "trace-existing"
    payload["correlation_id"] = "corr-existing"

    response = client.post("/brain/events", json=payload)

    assert response.status_code == 200
    assert response.json()["trace_id"] == "trace-existing"
    assert response.json()["correlation_id"] == "corr-existing"


def test_post_brain_events_does_not_auto_dispatch_by_default(
    fake_repository: FakeEventRepository,
    fake_publisher: NoopEventPublisher,
) -> None:
    """Event intake leaves router dispatch disabled by default."""
    fake_router = FakeEventReactionRouter()
    app.dependency_overrides[get_event_repository] = lambda: fake_repository
    app.dependency_overrides[get_event_publisher] = lambda: fake_publisher
    app.dependency_overrides[get_event_reaction_router_for_intake] = lambda: fake_router
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None,
        AION_EVENT_AUTO_DISPATCH_ENABLED=False,
    )
    try:
        response = TestClient(app).post("/brain/events", json=valid_event_payload())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert fake_router.requests == []


def test_post_brain_events_auto_dispatches_when_enabled(
    fake_repository: FakeEventRepository,
    fake_publisher: NoopEventPublisher,
) -> None:
    """Opt-in auto dispatch performs a best-effort router dispatch."""
    fake_router = FakeEventReactionRouter()
    app.dependency_overrides[get_event_repository] = lambda: fake_repository
    app.dependency_overrides[get_event_publisher] = lambda: fake_publisher
    app.dependency_overrides[get_event_reaction_router_for_intake] = lambda: fake_router
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None,
        AION_EVENT_AUTO_DISPATCH_ENABLED=True,
    )
    try:
        response = TestClient(app).post("/brain/events", json=valid_event_payload())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert len(fake_router.requests) == 1
    assert fake_router.requests[0].mode == "dry_run"
