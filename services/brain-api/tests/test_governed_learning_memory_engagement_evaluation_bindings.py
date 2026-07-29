from __future__ import annotations

from pathlib import Path

from scripts.lib import (
    governed_learning_memory_engagement_application_operator_evaluation as eval227,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_candidate_and_signal_binding_scenario_passed() -> None:
    report = eval227.validate_evaluation_report_file(
        REPO_ROOT
        / "examples/governed-learning-memory/engagement-application-operator-evaluation-report.json"
    )
    result = next(
        item for item in report["scenario_results"]
        if item["scenario_id"] == "candidate_and_signal_binding_integrity"
    )
    assert result["result"] == "passed"
    assert result["checks"]["binding_count"] == 9
    assert result["checks"]["changed_nested_candidate_rejected"] is True
