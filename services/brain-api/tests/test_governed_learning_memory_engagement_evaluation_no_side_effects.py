from __future__ import annotations

from pathlib import Path

from scripts.lib import (
    governed_learning_memory_engagement_application_operator_evaluation as eval227,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_aion227_evaluation_has_zero_side_effects() -> None:
    report = eval227.validate_evaluation_report_file(
        REPO_ROOT
        / "examples/governed-learning-memory/engagement-application-operator-evaluation-report.json"
    )
    for field in eval227.ZERO_EFFECT_FIELDS:
        assert report[field] == 0
    assert report["repository_unchanged"] is True
    assert report["temporary_evaluation_data_cleaned"] is True
