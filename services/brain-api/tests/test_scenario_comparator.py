"""Scenario comparator tests."""

from datetime import UTC, datetime

from aion_brain.contracts.scenarios import ScenarioRun
from aion_brain.scenarios.comparator import ScenarioComparator


def test_scenario_comparator_ignores_dynamic_fields() -> None:
    comparator = ScenarioComparator()

    result = comparator.compare_step_output(
        {"status": "ok", "created_at": "now", "trace_id": "trace-1"},
        {"equals": {"status": "ok"}},
    )

    assert result["passed"] is True


def test_scenario_comparator_detects_missing_required_key() -> None:
    comparator = ScenarioComparator()

    result = comparator.compare_step_output({"status": "ok"}, {"required_keys": ["value"]})

    assert result["passed"] is False
    assert "missing_required_key:value" in result["failures"]


def test_scenario_comparator_compares_run() -> None:
    run = ScenarioRun(
        scenario_run_id="run-1",
        scenario_id="scenario-1",
        status="passed",
        mode="dry_run",
        owner_scope=["workspace:main"],
        step_count=1,
        passed_steps=1,
        failed_steps=0,
        skipped_steps=0,
        steps=[],
        result={"status": "passed"},
        comparison={},
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )

    result = ScenarioComparator().compare_run(run, {"status": "passed", "min_count": 1})

    assert result["passed"] is True
