"""Freeze gate API tests."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.freeze import get_freeze_gate_service
from aion_brain.contracts.freeze import FreezeGateCheck, FreezeGateRun
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app


class FakeFreezeGateService:
    """Freeze gate service fake."""

    def __init__(self) -> None:
        self.run_record = _run()

    def run(self, request: object, *, app: object | None = None) -> FreezeGateRun:
        return self.run_record

    def get(self, freeze_gate_id: str, scope: list[str]) -> FreezeGateRun:
        return self.run_record

    def list(
        self,
        scope: list[str],
        *,
        version: str | None = None,
        status: str | None = None,
    ) -> list[FreezeGateRun]:
        return [self.run_record]


def test_freeze_gate_api_routes_work() -> None:
    app.dependency_overrides[get_freeze_gate_service] = lambda: FakeFreezeGateService()
    app.dependency_overrides[get_actor_context] = actor_context
    try:
        client = TestClient(app)
        run = client.post(
            "/brain/freeze-gate/run",
            json={"version": "0.1.0", "scope": ["workspace:main"]},
        )
        fetched = client.get("/brain/freeze-gate/freeze-1", params={"scope": "workspace:main"})
        listed = client.get("/brain/freeze-gate", params={"scope": "workspace:main"})
    finally:
        app.dependency_overrides.clear()

    assert run.status_code == 200
    assert fetched.status_code == 200
    assert listed.status_code == 200
    assert run.json()["status"] == "passed"


def actor_context() -> ActorContext:
    """Return dev actor context."""
    return ActorContext(
        actor_id="tester",
        actor_type="developer",
        workspace_id="main",
        roles=["owner"],
        permissions=["*"],
        security_scope=["workspace:main"],
        dev_mode=True,
    )


def _run() -> FreezeGateRun:
    check = FreezeGateCheck(
        check_id="check-1",
        name="unit",
        category="test",
        status="passed",
        severity="low",
        message="ok",
        details={},
    )
    return FreezeGateRun(
        freeze_gate_id="freeze-1",
        version="0.1.0",
        status="passed",
        requested_by="tester",
        checks=[check],
        failures=[],
        warnings=[],
        report={},
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
