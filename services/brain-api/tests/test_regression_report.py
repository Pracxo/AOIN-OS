"""Regression report tests."""

from datetime import UTC, datetime

from aion_brain.contracts.regression import RegressionRunResult
from aion_brain.contracts.replay import TraceComparison
from aion_brain.regression.report import RegressionReportBuilder


def test_report_uses_generic_recommendations() -> None:
    """Regression reports provide only generic architecture guidance."""
    comparison = TraceComparison(
        comparison_id="comparison-1",
        source_trace_id="trace-1",
        replay_trace_id="trace-2",
        source_snapshot_id="snapshot-1",
        replay_snapshot_id="snapshot-2",
        matched=False,
        drift_detected=True,
        score=0.5,
        differences=[
            {
                "path": "state.plan.steps[0].action_type",
                "source": "memory.retrieve",
                "replay": "memory.write",
                "severity": "high",
                "reason": "plan_action_changed",
            }
        ],
        ignored_fields=[],
        created_at=datetime.now(UTC),
    )
    result = RegressionRunResult(
        result_id="result-1",
        regression_run_id="run-1",
        case_id="case-1",
        replay_id="replay-1",
        status="failed",
        drift_detected=True,
        comparison=comparison,
    )
    report = RegressionReportBuilder().build([result])
    assert report["drift_detected"] == 1
    assert "review_planner_changes" in report["recommendations"]
