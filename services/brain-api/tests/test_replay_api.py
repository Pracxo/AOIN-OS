"""Replay and snapshot API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.replay import get_replay_service, get_snapshot_service
from aion_brain.contracts.replay import BrainSnapshot, ReplayRun
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app


class SnapshotAPI:
    def with_actor_context(self, actor_context):
        return self

    def create_snapshot(self, request):
        return snapshot(request.snapshot_id or "snapshot-1", request.snapshot_type, request.state)

    def create_trace_snapshot(self, trace_id, snapshot_type, scope, created_by=None):
        return snapshot("snapshot-trace", snapshot_type, {"trace": {"trace_id": trace_id}})

    def get_snapshot(self, snapshot_id, scope):
        return snapshot(snapshot_id, "full_trace", {"outcome": {"status": "planned"}})

    def list_snapshots(self, trace_id=None, snapshot_type=None, scope=None, limit=50):
        return [snapshot("snapshot-1", "full_trace", {"outcome": {"status": "planned"}})]


class ReplayAPI:
    def with_actor_context(self, actor_context):
        return self

    def replay(self, request):
        return replay_run(request.source_trace_id)

    def get_replay(self, replay_id, scope):
        return replay_run("trace-1", replay_id)


def test_snapshot_replay_and_compare_routes_work() -> None:
    """Snapshot, replay, and compare routes return AION contracts."""
    app.dependency_overrides[get_snapshot_service] = lambda: SnapshotAPI()
    app.dependency_overrides[get_replay_service] = lambda: ReplayAPI()
    app.dependency_overrides[get_actor_context] = actor_context
    client = TestClient(app)
    try:
        created = client.post(
            "/brain/snapshots",
            json={
                "owner_scope": ["workspace:main"],
                "snapshot_type": "full_trace",
                "state": {"outcome": {"status": "planned"}},
            },
        )
        traced = client.post(
            "/brain/snapshots/from-trace/trace-1",
            json={"snapshot_type": "full_trace", "scope": ["workspace:main"]},
        )
        listed = client.get("/brain/snapshots", params={"scope": "workspace:main"})
        replayed = client.post(
            "/brain/replay",
            json={"source_trace_id": "trace-1", "owner_scope": ["workspace:main"]},
        )
        compared = client.post(
            "/brain/replay/compare",
            json={
                "source_snapshot_id": "snapshot-1",
                "replay_snapshot_id": "snapshot-2",
                "scope": ["workspace:main"],
            },
        )
    finally:
        app.dependency_overrides.clear()
    assert created.status_code == 200
    assert traced.status_code == 200
    assert listed.status_code == 200
    assert replayed.status_code == 200
    assert compared.status_code == 200


def snapshot(snapshot_id: str, snapshot_type: str, state: dict) -> BrainSnapshot:
    return BrainSnapshot(
        snapshot_id=snapshot_id,
        trace_id="trace-1",
        owner_scope=["workspace:main"],
        snapshot_type=snapshot_type,
        state=state,
        content_hash="hash",
        created_at=datetime.now(UTC),
    )


def replay_run(source_trace_id: str, replay_id: str = "replay-1") -> ReplayRun:
    return ReplayRun(
        replay_id=replay_id,
        source_trace_id=source_trace_id,
        replay_trace_id="trace-replay",
        mode="dry_run",
        status="completed",
        input_snapshot_id="snapshot-1",
        output_snapshot_id="snapshot-2",
        comparison={},
        drift_detected=False,
        created_by="actor-1",
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )


def actor_context() -> ActorContext:
    return ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["owner"],
        permissions=["trace.read", "snapshot.create", "replay.run"],
        security_scope=["workspace:main"],
        dev_mode=True,
    )
