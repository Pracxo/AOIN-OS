"""Cognitive cycle repository tests."""

from datetime import UTC, datetime

from aion_brain.contracts.cycles import CognitiveCycleRunRequest, CognitiveCycleStepRun
from aion_brain.cycles.repository import CognitiveCycleRepository, new_run_from_request
from aion_brain.cycles.templates import build_sleep_consolidation_template


def test_cycle_repository_persists_template_run_step_and_sleep_record(tmp_path) -> None:
    """Repository stores templates, runs, steps, and sleep records."""
    repository = CognitiveCycleRepository(f"sqlite:///{tmp_path / 'cycles.db'}")
    template = build_sleep_consolidation_template(["workspace:main"])
    saved_template = repository.save_template(template)
    run = new_run_from_request(
        CognitiveCycleRunRequest(
            cycle_template_id=template.cycle_template_id,
            cycle_type="sleep_consolidation",
            owner_scope=["workspace:main"],
        ),
        "cycle-run-1",
        datetime.now(UTC),
    )
    saved_run = repository.save_run(run)
    step = repository.save_step(
        CognitiveCycleStepRun(
            cycle_step_run_id="cycle-step-1",
            cycle_run_id=saved_run.cycle_run_id,
            step_id="noop",
            step_type="noop",
            status="completed",
            input={},
            output={"ok": True},
            error={},
        )
    )

    fetched_template = repository.get_template(saved_template.cycle_template_id)
    fetched_run = repository.get_run(saved_run.cycle_run_id)
    listed = repository.list_runs(scope=["workspace:main"])

    assert fetched_template is not None
    assert fetched_template.steps[0].step_type == "attention_review"
    assert fetched_run is not None
    assert fetched_run.steps == [step]
    assert listed[0].cycle_run_id == "cycle-run-1"


def test_cycle_repository_filters_runs_by_scope(tmp_path) -> None:
    """Run listings only return records visible to requested scope."""
    repository = CognitiveCycleRepository(f"sqlite:///{tmp_path / 'cycles.db'}")
    run = new_run_from_request(
        CognitiveCycleRunRequest(cycle_type="review", owner_scope=["workspace:main"]),
        "cycle-run-1",
        datetime.now(UTC),
    )
    repository.save_run(run)

    assert len(repository.list_runs(scope=["workspace:main"])) == 1
    assert repository.list_runs(scope=["workspace:other"]) == []

