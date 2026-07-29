from __future__ import annotations

from pathlib import Path

import pytest
from scripts.lib import (
    governed_learning_memory_engagement_application_operator_evaluation as eval227,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _report() -> dict:
    return eval227.validate_evaluation_report_file(
        REPO_ROOT
        / "examples/governed-learning-memory/engagement-application-operator-evaluation-report.json"
    )


def test_all_required_aion227_scenarios_are_present_once() -> None:
    report = _report()
    assert tuple(report["scenario_ids"]) == eval227.SCENARIO_IDS
    actual = [item["scenario_id"] for item in report["scenario_results"]]
    assert actual == list(eval227.SCENARIO_IDS)
    assert len(actual) == len(set(actual)) == 28


def test_unknown_or_missing_hard_gate_rejects_report() -> None:
    payload = _report()
    payload["hard_gate_results"].pop(next(iter(payload["hard_gate_results"])))
    with pytest.raises(eval227.EvaluationError):
        eval227.validate_evaluation_report(payload)


def test_pass_cannot_survive_failed_hard_gate() -> None:
    payload = _report()
    gate = next(iter(payload["hard_gate_results"]))
    payload["hard_gate_results"][gate] = {"result": "failed", "passed": False}
    with pytest.raises(eval227.EvaluationError):
        eval227.validate_evaluation_report(payload)
