from __future__ import annotations

from pathlib import Path

from scripts.lib import (
    governed_learning_memory_engagement_application_operator_evaluation as eval227,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_approval_scenarios_preserve_separation_of_duties() -> None:
    report = eval227.validate_evaluation_report_file(
        REPO_ROOT
        / "examples/governed-learning-memory/engagement-application-operator-evaluation-report.json"
    )
    low = next(
        item for item in report["scenario_results"]
        if item["scenario_id"] == "low_risk_single_independent_approval"
    )
    elevated = next(
        item for item in report["scenario_results"]
        if item["scenario_id"] == "elevated_risk_dual_approval_and_separation_of_duties"
    )
    assert low["result"] == "passed"
    assert elevated["result"] == "passed"
    assert all(elevated["checks"].values())
