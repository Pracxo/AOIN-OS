"""Event intake idempotency and outbox integration tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.attention import get_attention_controller
from aion_brain.api.events import (
    get_event_publisher,
    get_event_reaction_router_for_intake,
    get_event_repository,
    get_idempotency_service_for_intake,
    get_outbox_service_for_intake,
)
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.events import AIONEvent
from aion_brain.idempotency.repository import IdempotencyRepository
from aion_brain.idempotency.service import IdempotencyService
from aion_brain.main import app


class FakeEventRepository:
    """Event repository fake."""

    def __init__(self) -> None:
        self.events: list[AIONEvent] = []

    def save(self, event: AIONEvent) -> AIONEvent:
        self.events.append(event)
        return event


class FakePublisher:
    """Publisher fake."""

    def publish(self, event: AIONEvent) -> bool:
        return True


class FakeAttention:
    """Attention fake."""

    def create_signal(self, request: object) -> None:
        return None


class FakeOutbox:
    """Outbox fake."""

    def __init__(self) -> None:
        self.requests: list[object] = []

    def enqueue(self, request: object) -> object:
        self.requests.append(request)
        return object()


def test_event_intake_idempotency_prevents_duplicate_persisted_event() -> None:
    """Same idempotency key and payload does not persist twice."""
    repository = FakeEventRepository()
    outbox = FakeOutbox()
    idempotency = IdempotencyService(
        IdempotencyRepository(database_url="sqlite+pysqlite:///:memory:")
    )
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
    )
    app.dependency_overrides[get_event_repository] = lambda: repository
    app.dependency_overrides[get_event_publisher] = lambda: FakePublisher()
    app.dependency_overrides[get_attention_controller] = lambda: FakeAttention()
    app.dependency_overrides[get_event_reaction_router_for_intake] = lambda: None
    app.dependency_overrides[get_idempotency_service_for_intake] = lambda: idempotency
    app.dependency_overrides[get_outbox_service_for_intake] = lambda: outbox
    try:
        client = TestClient(app)
        payload = event_payload()
        headers = {"X-AION-Idempotency-Key": "idem-event-1"}

        first = client.post("/brain/events", json=payload, headers=headers)
        second = client.post("/brain/events", json=payload, headers=headers)

        assert first.status_code == 200
        assert second.status_code == 200
        assert len(repository.events) == 1
    finally:
        app.dependency_overrides.clear()


def test_event_intake_enqueues_outbox_message_for_nats_publish() -> None:
    """Persisted events enqueue a NATS outbox message where practical."""
    repository = FakeEventRepository()
    outbox = FakeOutbox()
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
    )
    app.dependency_overrides[get_event_repository] = lambda: repository
    app.dependency_overrides[get_event_publisher] = lambda: FakePublisher()
    app.dependency_overrides[get_attention_controller] = lambda: FakeAttention()
    app.dependency_overrides[get_event_reaction_router_for_intake] = lambda: None
    app.dependency_overrides[get_idempotency_service_for_intake] = lambda: None
    app.dependency_overrides[get_outbox_service_for_intake] = lambda: outbox
    try:
        client = TestClient(app)
        response = client.post("/brain/events", json=event_payload())

        assert response.status_code == 200
        assert outbox.requests
    finally:
        app.dependency_overrides.clear()


def event_payload() -> dict[str, object]:
    return {
        "event_id": "event-1",
        "source": "test",
        "event_type": "generic.created",
        "payload_type": "json",
        "payload": {"value": 1},
        "timestamp": datetime.now(UTC).isoformat(),
        "security_scope": ["workspace:main"],
    }
