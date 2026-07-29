from __future__ import annotations

from pathlib import Path

from scripts.lib import (
    governed_learning_memory_engagement_application_operator_evaluation as eval227,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_lifecycle_scenario_preserves_rejections_and_expiry() -> None:
    report = eval227.validate_evaluation_report_file(
        REPO_ROOT
        / "examples/governed-learning-memory/engagement-application-operator-evaluation-report.json"
    )
    result = next(
        item for item in report["scenario_results"]
        if item["scenario_id"] == "lifecycle_expiry_supersession_retraction_and_rejection"
    )
    assert result["result"] == "passed"
    assert result["checks"]["operator_review_rejected"] is True
    assert result["checks"]["expired"] is True
