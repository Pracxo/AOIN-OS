"""Actor context integration tests for existing Brain routes."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.brain import get_brain_loop_service
from aion_brain.api.events import get_event_publisher, get_event_repository
from aion_brain.api.memory import get_memory_service
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.memory import MemoryRetrievalRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app


class FakeEventRepository:
    """Event repository fake."""

    def __init__(self) -> None:
        self.event: AIONEvent | None = None

    def save(self, event: AIONEvent) -> AIONEvent:
        self.event = event
        return event


class FakePublisher:
    """Event publisher fake."""

    def publish(self, event: AIONEvent) -> bool:
        return True


class FakeMemoryService:
    """Memory service fake."""

    def __init__(self) -> None:
        self.request: MemoryRetrievalRequest | None = None

    def retrieve(self, request: MemoryRetrievalRequest) -> list[object]:
        self.request = request
        return []


class FakeBrainLoopService:
    """Brain loop service fake."""

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
                "status": "planned",
                "actor_id": event.actor_id,
                "workspace_id": event.workspace_id,
                "security_scope": event.security_scope,
                "permission_context_present": True,
            },
            created_at=datetime.now(UTC),
        )


def test_events_use_actor_context_when_actor_fields_missing() -> None:
    """Event intake fills actor, workspace, scope, trace, and correlation defaults."""
    repository = FakeEventRepository()
    app.dependency_overrides[get_event_repository] = lambda: repository
    app.dependency_overrides[get_event_publisher] = lambda: FakePublisher()
    app.dependency_overrides[get_actor_context] = actor_context
    try:
        response = TestClient(app).post(
            "/brain/events",
            json={
                "event_id": "event-ctx",
                "source": "test",
                "event_type": "test.received",
                "payload_type": "test.payload",
                "payload": {},
                "timestamp": "2026-06-07T09:00:00Z",
                "security_scope": [],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert repository.event is not None
    assert repository.event.actor_id == "actor-ctx"
    assert repository.event.workspace_id == "workspace-ctx"
    assert repository.event.security_scope == ["workspace:workspace-ctx"]
    assert repository.event.trace_id == "trace-ctx"


def test_memory_retrieve_uses_actor_context_scope_when_scope_missing() -> None:
    """Memory retrieve falls back to ActorContext security scope."""
    service = FakeMemoryService()
    app.dependency_overrides[get_memory_service] = lambda: service
    app.dependency_overrides[get_actor_context] = actor_context
    try:
        response = TestClient(app).post(
            "/brain/memory/retrieve",
            json={"query": "alpha", "scope": [], "limit": 10, "memory_types": []},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert service.request is not None
    assert service.request.scope == ["workspace:workspace-ctx"]


def test_brain_think_includes_actor_context_metadata() -> None:
    """Brain think sends actor context into the Brain loop."""
    service = FakeBrainLoopService()
    app.dependency_overrides[get_brain_loop_service] = lambda: service
    app.dependency_overrides[get_actor_context] = actor_context
    try:
        response = TestClient(app).post(
            "/brain/think",
            json={
                "event_id": "event-think",
                "source": "test",
                "event_type": "question.answer",
                "payload_type": "test.payload",
                "payload": {"question": "what"},
                "timestamp": "2026-06-07T09:00:00Z",
                "security_scope": [],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["outcome"]["actor_id"] == "actor-ctx"
    assert service.event is not None
    assert service.event.workspace_id == "workspace-ctx"


def actor_context() -> ActorContext:
    """Return a test actor context."""
    return ActorContext(
        actor_id="actor-ctx",
        workspace_id="workspace-ctx",
        roles=["owner"],
        permissions=["brain.think"],
        security_scope=["workspace:workspace-ctx"],
        correlation_id="corr-ctx",
        trace_id="trace-ctx",
        dev_mode=True,
    )
