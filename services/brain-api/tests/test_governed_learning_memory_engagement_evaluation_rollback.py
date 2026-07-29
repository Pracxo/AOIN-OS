from __future__ import annotations

from pathlib import Path

from scripts.lib import (
    governed_learning_memory_engagement_application_operator_evaluation as eval227,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_expiry_rollback_cleanup_scenario_leaves_zero_active_overlays() -> None:
    report = eval227.validate_evaluation_report_file(
        REPO_ROOT
        / "examples/governed-learning-memory/engagement-application-operator-evaluation-report.json"
    )
    result = next(
        item for item in report["scenario_results"]
        if item["scenario_id"] == "expiry_rollback_and_session_cleanup"
    )
    assert result["result"] == "passed"
    assert result["checks"]["active_overlay_count_after_close"] == 0
    assert result["checks"]["rollback_restores_baseline_view"] is True
