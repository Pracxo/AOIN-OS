"""Cognitive cycle API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.cycles import get_cycle_orchestrator
from aion_brain.contracts.cycles import (
    CognitiveCycleRun,
    CognitiveCycleRunRequest,
    CognitiveCycleTemplate,
    CycleStatus,
    SleepConsolidationRecord,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app


class FakeCycleOrchestrator:
    """Cycle orchestrator fake for API tests."""

    def __init__(self) -> None:
        self.template = make_template()
        self.run = make_run()
        self.record = make_sleep_record()

    def create_template(self, template: CognitiveCycleTemplate) -> CognitiveCycleTemplate:
        self.template = template
        return template

    def list_templates(
        self,
        cycle_type: str | None = None,
        status: str | None = None,
    ) -> list[CognitiveCycleTemplate]:
        return [self.template]

    def disable_template(
        self,
        cycle_template_id: str,
        actor_id: str | None,
        reason: str,
    ) -> CognitiveCycleTemplate:
        return self.template.model_copy(update={"status": "disabled"})

    def run_cycle(self, request: CognitiveCycleRunRequest) -> CognitiveCycleRun:
        self.run = self.run.model_copy(
            update={
                "cycle_type": request.cycle_type,
                "mode": request.mode,
                "owner_scope": request.owner_scope,
                "actor_id": request.actor_id,
                "workspace_id": request.workspace_id,
                "input": request.input,
            }
        )
        return self.run

    def get_run(self, cycle_run_id: str, scope: list[str]) -> CognitiveCycleRun | None:
        return self.run if cycle_run_id == self.run.cycle_run_id and scope else None

    def list_runs(
        self,
        scope: list[str],
        cycle_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[CognitiveCycleRun]:
        return [self.run][:limit]

    def status(self, cycle_type: str, scope: list[str]) -> CycleStatus:
        return CycleStatus(
            cycle_type=cycle_type,  # type: ignore[arg-type]
            latest_run=self.run,
            active_run_count=0,
            completed_run_count=1,
            failed_run_count=0,
            generated_at=datetime.now(UTC),
        )

    def get_sleep_record(
        self,
        cycle_run_id: str,
        scope: list[str],
    ) -> SleepConsolidationRecord | None:
        return self.record if cycle_run_id == self.record.cycle_run_id and scope else None


def test_cycles_api_template_and_run_endpoints() -> None:
    """Cycle API exposes template and run operations."""
    orchestrator = FakeCycleOrchestrator()
    with cycle_overrides(orchestrator):
        client = TestClient(app)
        template = client.post("/brain/cycles/templates", json=template_payload())
        templates = client.get("/brain/cycles/templates")
        disabled = client.post(
            "/brain/cycles/templates/template-1/disable",
            json={"reason": "No longer needed."},
        )
        run = client.post(
            "/brain/cycles/run",
            json={
                "cycle_type": "review",
                "owner_scope": ["workspace:main"],
                "input": {},
            },
        )
        fetched = client.get("/brain/cycles/runs/cycle-run-1", params={"scope": "workspace:main"})
        listed = client.get("/brain/cycles/runs", params={"scope": "workspace:main"})

    assert template.status_code == 200
    assert templates.status_code == 200
    assert disabled.json()["status"] == "disabled"
    assert run.json()["actor_id"] == "actor-1"
    assert run.json()["input"]["approval_present"] is False
    assert fetched.status_code == 200
    assert listed.json()[0]["cycle_run_id"] == "cycle-run-1"


def test_cycles_api_sleep_status_and_record_endpoints() -> None:
    """Sleep consolidation convenience endpoint and status endpoints work."""
    with cycle_overrides(FakeCycleOrchestrator()):
        client = TestClient(app)
        sleep = client.post("/brain/cycles/sleep-consolidation", json={})
        status = client.get("/brain/cycles/status/sleep_consolidation")
        record = client.get(
            "/brain/cycles/sleep-consolidation/cycle-run-1",
            params={"scope": "workspace:main"},
        )

    assert sleep.status_code == 200
    assert sleep.json()["cycle_type"] == "sleep_consolidation"
    assert sleep.json()["mode"] == "dry_run"
    assert status.json()["completed_run_count"] == 1
    assert record.json()["summary"] == "Sleep consolidation completed deterministically."


def cycle_overrides(orchestrator: FakeCycleOrchestrator) -> object:
    """Install cycle API dependency overrides for one context."""

    class OverrideContext:
        def __enter__(self) -> None:
            app.dependency_overrides[get_cycle_orchestrator] = lambda: orchestrator
            app.dependency_overrides[get_actor_context] = lambda: ActorContext(
                actor_id="actor-1",
                workspace_id="workspace-1",
                security_scope=["workspace:main"],
                trace_id="trace-1",
                dev_mode=True,
            )

        def __exit__(self, *args: object) -> None:
            app.dependency_overrides.clear()

    return OverrideContext()


def make_template() -> CognitiveCycleTemplate:
    """Create a cycle template contract."""
    return CognitiveCycleTemplate(
        cycle_template_id="template-1",
        name="Generic cycle",
        description="Review local Brain state.",
        cycle_type="review",
        status="active",
        owner_scope=["workspace:main"],
        steps=[
            {
                "step_id": "noop",
                "step_type": "noop",
                "description": "No operation.",
            }
        ],
        risk_level="low",
        requires_approval=False,
        metadata={},
    )


def make_run() -> CognitiveCycleRun:
    """Create a cycle run contract."""
    return CognitiveCycleRun(
        cycle_run_id="cycle-run-1",
        trace_id="trace-1",
        actor_id="actor-1",
        workspace_id="workspace-1",
        cycle_type="review",
        status="completed",
        mode="dry_run",
        owner_scope=["workspace:main"],
        steps=[],
        input={},
        output={},
        error={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def make_sleep_record() -> SleepConsolidationRecord:
    """Create a sleep consolidation record."""
    return SleepConsolidationRecord(
        consolidation_id="sleep-consolidation-1",
        cycle_run_id="cycle-run-1",
        trace_id="trace-1",
        actor_id="actor-1",
        workspace_id="workspace-1",
        owner_scope=["workspace:main"],
        working_memory_slots_reviewed=0,
        memories_decayed=0,
        conflicts_detected=0,
        compaction_runs=0,
        reflections_created=0,
        skill_candidates_created=0,
        regression_cases_checked=0,
        visual_snapshots_created=0,
        summary="Sleep consolidation completed deterministically.",
        result={"dry_run": True},
        created_at=datetime.now(UTC),
    )


def template_payload() -> dict[str, object]:
    """Return a cycle template payload."""
    return make_template().model_dump(mode="json")
