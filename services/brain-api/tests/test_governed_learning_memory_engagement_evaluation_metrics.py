from __future__ import annotations

from pathlib import Path

from scripts.lib import (
    governed_learning_memory_engagement_application_operator_evaluation as eval227,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_metric_scenario_keeps_quality_gain_bounded() -> None:
    report = eval227.validate_evaluation_report_file(
        REPO_ROOT
        / "examples/governed-learning-memory/engagement-application-operator-evaluation-report.json"
    )
    result = next(
        item for item in report["scenario_results"]
        if item["scenario_id"] == "metric_registry_direction_and_delta_integrity"
    )
    assert result["result"] == "passed"
    assert result["checks"]["metric_improvement_implies_factual_correctness"] is False
