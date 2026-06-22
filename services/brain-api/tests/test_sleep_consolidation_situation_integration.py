from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.cycles import CognitiveCycleRun
from aion_brain.cycles.sleep import SleepConsolidationService
from tests.situation_helpers import bundle


def test_sleep_consolidation_runs_situation_projection_dry_run() -> None:
    services = bundle()
    cycle_run = CognitiveCycleRun(
        cycle_run_id="cycle-run-1",
        trace_id="trace-1",
        actor_id="actor-1",
        workspace_id="workspace-1",
        cycle_type="sleep_consolidation",
        status="running",
        mode="dry_run",
        owner_scope=["workspace:main"],
        created_at=datetime.now(UTC),
    )

    record = SleepConsolidationService(situation_projector=services.projector).run(
        cycle_run,
        dry_run=True,
    )

    assert record.result["situation_projection"]["status"] == "dry_run"
