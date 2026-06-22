"""Visual Brain Projection API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.visual import (
    get_trace_timeline_builder,
    get_visual_projection_service,
    get_visual_query_service,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.visual import (
    BrainMap,
    BrainMapSnapshot,
    TraceTimeline,
)
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app
from tests.test_visual_service import telemetry


class FakeProjectionService:
    """Visual projection service fake."""

    def with_actor_context(self, actor_context: ActorContext):
        return self

    def build_map(self, request):
        return brain_map(request.trace_id)

    def create_snapshot(self, request):
        item = brain_map(request.trace_id)
        return BrainMapSnapshot(
            snapshot_id="snapshot-1",
            trace_id=request.trace_id,
            workspace_id=request.workspace_id,
            owner_scope=request.scope,
            map=item,
            node_count=0,
            edge_count=0,
            pulse_count=0,
            created_at=datetime.now(UTC),
        )

    def get_snapshot(self, snapshot_id: str, scope: list[str]):
        item = brain_map("trace-1")
        return BrainMapSnapshot(
            snapshot_id=snapshot_id,
            trace_id="trace-1",
            workspace_id="workspace-1",
            owner_scope=scope,
            map=item,
            node_count=0,
            edge_count=0,
            pulse_count=0,
            created_at=datetime.now(UTC),
        )


class FakeQueryService:
    """Visual telemetry query service fake."""

    def with_actor_context(self, actor_context: ActorContext):
        return self

    def query(self, query):
        return [telemetry()]

    def get_recent(self, scope: list[str], limit: int):
        return [telemetry()]

    def authorize_stream(self, trace_id: str | None, scope: list[str]) -> None:
        return None


class FakeTimelineBuilder:
    """Timeline builder fake."""

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


def test_visual_api_routes_work() -> None:
    """Map, snapshot, telemetry, timeline, and SSE routes return AION contracts."""
    app.dependency_overrides[get_visual_projection_service] = lambda: FakeProjectionService()
    app.dependency_overrides[get_visual_query_service] = lambda: FakeQueryService()
    app.dependency_overrides[get_trace_timeline_builder] = lambda: FakeTimelineBuilder()
    app.dependency_overrides[get_actor_context] = actor_context
    payload = {"trace_id": "trace-1", "workspace_id": "workspace-1", "scope": ["workspace:main"]}
    try:
        client = TestClient(app)
        map_response = client.post("/brain/visual/map", json=payload)
        trace_map = client.get(
            "/brain/visual/map/traces/trace-1",
            params={"scope": "workspace:main"},
        )
        snapshot = client.post("/brain/visual/snapshots", json=payload)
        snapshot_get = client.get(
            "/brain/visual/snapshots/snapshot-1",
            params={"scope": "workspace:main"},
        )
        query = client.post(
            "/brain/visual/telemetry/query",
            json={"trace_id": "trace-1", "scope": ["workspace:main"]},
        )
        recent = client.get(
            "/brain/visual/telemetry/recent",
            params={"scope": "workspace:main", "limit": 1},
        )
        timeline = client.post(
            "/brain/visual/timeline",
            json={"trace_id": "trace-1", "scope": ["workspace:main"]},
        )
        timeline_get = client.get(
            "/brain/visual/timeline/trace-1",
            params={"scope": "workspace:main"},
        )
        stream = client.get(
            "/brain/visual/stream",
            params={"scope": "workspace:main", "max_events": 1},
        )
    finally:
        app.dependency_overrides.clear()

    assert map_response.status_code == 200
    assert trace_map.status_code == 200
    assert snapshot.status_code == 200
    assert snapshot_get.status_code == 200
    assert query.status_code == 200
    assert recent.status_code == 200
    assert timeline.status_code == 200
    assert timeline_get.status_code == 200
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    assert "event: visual_telemetry" in stream.text


def brain_map(trace_id: str | None) -> BrainMap:
    return BrainMap(
        map_id="map-1",
        trace_id=trace_id,
        workspace_id="workspace-1",
        nodes=[],
        edges=[],
        pulses=[],
        clusters=[],
        stats={},
        created_at=datetime.now(UTC),
    )


def actor_context() -> ActorContext:
    return ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["owner"],
        permissions=["trace.read", "telemetry.read", "visual.stream.read"],
        security_scope=["workspace:main"],
        dev_mode=True,
    )
