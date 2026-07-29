from __future__ import annotations

from pathlib import Path

from scripts.lib import (
    governed_learning_memory_engagement_application_operator_evaluation as eval227,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_aion227_evaluation_docs_and_report_exist() -> None:
    for relative in (
        "docs/governed-learning-memory/engagement-application-operator-evaluation-closeout.md",
        "docs/governed-learning-memory/engagement-application-operator-evaluation-report.md",
        "docs/governed-learning-memory/engagement-evaluation-scenarios.md",
        "docs/governed-learning-memory/engagement-evaluation-security-boundary.md",
        "examples/governed-learning-memory/engagement-application-operator-evaluation-report.json",
    ):
        assert (REPO_ROOT / relative).is_file()


def test_aion227_evaluation_report_is_exact_pass() -> None:
    report = eval227.validate_evaluation_report_file(
        REPO_ROOT
        / "examples/governed-learning-memory/engagement-application-operator-evaluation-report.json"
    )
    assert report["evaluation_id"] == "AION-GLMPE-003"
    assert report["decision"] == eval227.PASS_DECISION
    assert report["evaluation_passed"] is True
    assert report["scenario_count"] == 28
