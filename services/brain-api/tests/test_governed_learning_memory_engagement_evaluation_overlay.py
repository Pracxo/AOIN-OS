from __future__ import annotations

from pathlib import Path

from scripts.lib import (
    governed_learning_memory_engagement_application_operator_evaluation as eval227,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_overlay_scenario_remains_in_memory_and_copy_on_write() -> None:
    report = eval227.validate_evaluation_report_file(
        REPO_ROOT
        / "examples/governed-learning-memory/engagement-application-operator-evaluation-report.json"
    )
    result = next(
        item for item in report["scenario_results"]
        if item["scenario_id"] == "immutable_overlay_and_copy_on_write_repository"
    )
    assert result["result"] == "passed"
    assert result["checks"]["copy_on_write"] is True
    assert result["checks"]["has_save_method"] is False
    assert result["checks"]["has_update_method"] is False
    assert result["checks"]["has_delete_method"] is False
