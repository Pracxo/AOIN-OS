from __future__ import annotations

from pathlib import Path

from scripts.lib import (
    governed_learning_memory_engagement_application_operator_evaluation as eval227,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_risk_mapping_scenario_enforces_fixed_registry() -> None:
    report = eval227.validate_evaluation_report_file(
        REPO_ROOT
        / "examples/governed-learning-memory/engagement-application-operator-evaluation-report.json"
    )
    result = next(
        item for item in report["scenario_results"]
        if item["scenario_id"] == "fixed_target_mapping_operation_and_risk"
    )
    assert result["result"] == "passed"
    low = [item for item in result["checks"].values() if item["risk_class"] == "low"]
    elevated = [
        item for item in result["checks"].values() if item["risk_class"] == "elevated"
    ]
    assert len(low) == 4
    assert len(elevated) == 5
