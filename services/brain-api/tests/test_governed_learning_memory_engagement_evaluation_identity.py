from __future__ import annotations

from pathlib import Path

from scripts.lib import (
    governed_learning_memory_engagement_application_operator_evaluation as eval227,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_adaptation_identity_scenario_is_deterministic() -> None:
    report = eval227.validate_evaluation_report_file(
        REPO_ROOT
        / "examples/governed-learning-memory/engagement-application-operator-evaluation-report.json"
    )
    result = next(
        item for item in report["scenario_results"]
        if item["scenario_id"] == "deterministic_adaptation_identity"
    )
    assert result["result"] == "passed"
    assert result["checks"]["changed_subject_changes_identity"] is True
    assert result["checks"]["approval_not_in_base_identity"] is True
