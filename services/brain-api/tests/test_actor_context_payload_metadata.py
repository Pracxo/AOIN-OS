"""AION-160 payload actor metadata remains unverified domain metadata."""

from fastapi.testclient import TestClient

from aion_brain.api.events import get_event_publisher, get_event_repository
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.events import AIONEvent
from aion_brain.main import app


class FakeEventRepository:
    def __init__(self) -> None:
        self.event: AIONEvent | None = None

    def save(self, event: AIONEvent) -> AIONEvent:
        self.event = event
        return event


class FakePublisher:
    def publish(self, event: AIONEvent) -> bool:
        return True


def test_payload_actor_metadata_is_preserved_but_not_authenticated() -> None:
    repository = FakeEventRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(
        env="production",
        dev_auth_enabled=True,
    )
    app.dependency_overrides[get_event_repository] = lambda: repository
    app.dependency_overrides[get_event_publisher] = lambda: FakePublisher()
    try:
        response = TestClient(app).post(
            "/brain/events",
            headers={
                "X-AION-Actor-ID": "root",
                "X-AION-Workspace-ID": "system",
                "X-AION-Permissions": "*",
            },
            json={
                "event_id": "event-payload-a160",
                "source": "test",
                "event_type": "test.received",
                "payload_type": "test.payload",
                "payload": {"actor_metadata_classification": "unverified_domain_metadata"},
                "timestamp": "2026-07-17T00:00:00Z",
                "actor_id": "payload-actor",
                "workspace_id": "payload-workspace",
                "security_scope": [],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert repository.event is not None
    assert repository.event.actor_id == "payload-actor"
    assert repository.event.workspace_id == "payload-workspace"
    assert repository.event.security_scope == []
