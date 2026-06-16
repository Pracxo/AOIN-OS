"""Release baseline API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.release_baseline import get_release_baseline_service
from aion_brain.contracts.release_baseline import ReleaseBaselineReport
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app


class FakeReleaseBaselineService:
    def run(self, request):
        return report(request.release_baseline_id or "baseline-1")

    def get(self, release_baseline_id: str, scope: list[str]):
        return report(release_baseline_id)

    def list(self, *, scope, version=None, status=None, limit=50):
        return [report("baseline-1")]


def test_release_baseline_api_routes_work() -> None:
    app.dependency_overrides[get_release_baseline_service] = lambda: FakeReleaseBaselineService()
    app.dependency_overrides[get_actor_context] = actor_context
    try:
        client = TestClient(app)
        run = client.post(
            "/brain/release-baseline/run",
            json={"version": "0.1.0", "owner_scope": ["workspace:main"]},
        )
        get = client.get(
            "/brain/release-baseline/baseline-1",
            params={"scope": "workspace:main"},
        )
        listing = client.get(
            "/brain/release-baseline",
            params={"scope": "workspace:main"},
        )
    finally:
        app.dependency_overrides.clear()

    assert run.status_code == 200
    assert get.status_code == 200
    assert listing.status_code == 200


def report(release_baseline_id: str) -> ReleaseBaselineReport:
    now = datetime.now(UTC)
    return ReleaseBaselineReport(
        release_baseline_id=release_baseline_id,
        version="0.1.0",
        status="passed",
        scenario_run_ids=["run-1"],
        quality_gate_results={},
        report={"release_ready": True},
        created_at=now,
        completed_at=now,
    )


def actor_context() -> ActorContext:
    return ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["owner"],
        permissions=["release_baseline.run", "release_baseline.read"],
        security_scope=["workspace:main"],
        dev_mode=True,
    )
