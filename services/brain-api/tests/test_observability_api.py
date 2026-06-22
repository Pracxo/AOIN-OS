"""Observability API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.observability import get_observability_service
from aion_brain.api.visual import get_trace_timeline_builder
from aion_brain.contracts.observability import ObservabilitySummary
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.visual import TraceTimeline
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app
from tests.test_observability_contracts import event


class FakeObservabilityService:
    """Observability service fake."""

    def with_actor_context(self, actor_context: ActorContext):
        return self

    def record_event(self, item):
        return item.model_copy(update={"created_at": datetime.now(UTC)})

    def summarize(self, scope: list[str]):
        return ObservabilitySummary(
            trace_count=1,
            telemetry_event_count=2,
            observability_event_count=3,
            active_node_count=2,
            blocked_event_count=0,
            failed_event_count=0,
            latest_trace_id="trace-1",
            generated_at=datetime.now(UTC),
        )


class FakeTimelineBuilder:
    def with_actor_context(self, actor_context: ActorContext):
        return self

    def build(self, request):
        return TraceTimeline(
            timeline_id="timeline-1",
            trace_id=request.trace_id,
            owner_scope=request.scope,
            events=[],
            duration_ms=None,
            status="completed",
            created_at=datetime.now(UTC),
        )


def test_observability_api_routes_work() -> None:
    """Local event, summary, and timeline alias routes work."""
    app.dependency_overrides[get_observability_service] = lambda: FakeObservabilityService()
    app.dependency_overrides[get_trace_timeline_builder] = lambda: FakeTimelineBuilder()
    app.dependency_overrides[get_actor_context] = lambda: ActorContext(
        actor_id="actor-1",
        roles=["owner"],
        security_scope=["workspace:main"],
        dev_mode=True,
    )
    try:
        client = TestClient(app)
        recorded = client.post(
            "/brain/observability/events",
            json=event().model_dump(mode="json"),
        )
        summary = client.get(
            "/brain/observability/summary",
            params={"scope": "workspace:main"},
        )
        timeline = client.get(
            "/brain/observability/traces/trace-1/timeline",
            params={"scope": "workspace:main"},
        )
    finally:
        app.dependency_overrides.clear()

    assert recorded.status_code == 200
    assert summary.status_code == 200
    assert summary.json()["observability_event_count"] == 3
    assert timeline.status_code == 200
