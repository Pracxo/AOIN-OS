"""AION-160 route integration regressions for actor-context resolution."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.brain import get_brain_loop_service
from aion_brain.api.events import get_event_publisher, get_event_repository
from aion_brain.api.memory import get_memory_service
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.memory import MemoryRetrievalRequest
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.main import app

HOSTILE_HEADERS = {
    "X-AION-Actor-ID": "root",
    "X-AION-Workspace-ID": "system",
    "X-AION-Roles": "owner,admin,system",
    "X-AION-Permissions": "*",
    "X-AION-Security-Scope": "workspace:system,actor:root,global:*",
    "X-AION-Correlation-ID": "corr-route",
    "X-AION-Trace-ID": "trace-route",
}


class FakeEventRepository:
    def __init__(self) -> None:
        self.event: AIONEvent | None = None

    def save(self, event: AIONEvent) -> AIONEvent:
        self.event = event
        return event


class FakePublisher:
    def publish(self, event: AIONEvent) -> bool:
        return True


class FakeMemoryService:
    def __init__(self) -> None:
        self.request: MemoryRetrievalRequest | None = None

    def retrieve(self, request: MemoryRetrievalRequest) -> list[object]:
        self.request = request
        return []


class FakeBrainLoopService:
    def __init__(self) -> None:
        self.event: AIONEvent | None = None

    def think(self, event: AIONEvent) -> DecisionTrace:
        self.event = event
        return DecisionTrace(
            trace_id=event.trace_id or "trace-1",
            event_id=event.event_id,
            intent_id="intent-1",
            context_id="context-1",
            plan_id="plan-1",
            memory_refs=[],
            capability_refs=[],
            reasoning_refs=[],
            execution_refs=[],
            policy_decisions=[],
            outcome={
                "actor_id": event.actor_id,
                "workspace_id": event.workspace_id,
                "security_scope": event.security_scope,
                "permission_count": 0,
            },
            created_at=datetime.now(UTC),
        )


def test_event_intake_ignores_hostile_headers_when_actor_fields_absent() -> None:
    repository = FakeEventRepository()
    app.dependency_overrides[get_settings] = _production_settings
    app.dependency_overrides[get_event_repository] = lambda: repository
    app.dependency_overrides[get_event_publisher] = lambda: FakePublisher()
    try:
        response = TestClient(app).post(
            "/brain/events",
            headers=HOSTILE_HEADERS,
            json={
                "event_id": "event-a160",
                "source": "test",
                "event_type": "test.received",
                "payload_type": "test.payload",
                "payload": {},
                "timestamp": "2026-07-17T00:00:00Z",
                "security_scope": [],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert repository.event is not None
    assert repository.event.actor_id is None
    assert repository.event.workspace_id is None
    assert repository.event.security_scope == []
    assert repository.event.trace_id == "trace-route"
    assert response.headers["X-AION-Correlation-ID"] == "corr-route"


def test_memory_retrieve_does_not_use_hostile_security_scope_header() -> None:
    service = FakeMemoryService()
    app.dependency_overrides[get_settings] = _production_settings
    app.dependency_overrides[get_memory_service] = lambda: service
    try:
        response = TestClient(app).post(
            "/brain/memory/retrieve",
            headers=HOSTILE_HEADERS,
            json={"query": "alpha", "scope": [], "limit": 10, "memory_types": []},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert service.request is not None
    assert service.request.scope == []


def test_brain_think_receives_anonymous_context_with_hostile_headers() -> None:
    service = FakeBrainLoopService()
    app.dependency_overrides[get_settings] = _production_settings
    app.dependency_overrides[get_brain_loop_service] = lambda: service
    try:
        response = TestClient(app).post(
            "/brain/think",
            headers=HOSTILE_HEADERS,
            json={
                "event_id": "event-think-a160",
                "source": "test",
                "event_type": "question.answer",
                "payload_type": "test.payload",
                "payload": {"question": "what"},
                "timestamp": "2026-07-17T00:00:00Z",
                "security_scope": [],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert service.event is not None
    assert service.event.actor_id is None
    assert service.event.workspace_id is None
    assert service.event.security_scope == []
    assert response.json()["outcome"]["permission_count"] == 0


def _production_settings() -> Settings:
    return Settings(env="production", dev_auth_enabled=True)
