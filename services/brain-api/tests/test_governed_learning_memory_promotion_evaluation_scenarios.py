from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from scripts.lib import governed_learning_memory_promotion_operator_evaluation as evaluation


def test_evaluation_report_rejects_duplicate_scenarios(tmp_path: Path) -> None:
    report = evaluation.build_report(
        evaluation_id=evaluation.EVALUATION_ID,
        evaluation_base_commit="unit-test-base",
        tmp_dir=tmp_path,
    )
    report["scenario_results"][1]["scenario_id"] = report["scenario_results"][0]["scenario_id"]

    with pytest.raises(evaluation.EvaluationReportError):
        evaluation.validate_evaluation_report(report)


def test_evaluation_report_rejects_unknown_scenarios(tmp_path: Path) -> None:
    report = evaluation.build_report(
        evaluation_id=evaluation.EVALUATION_ID,
        evaluation_base_commit="unit-test-base",
        tmp_dir=tmp_path,
    )
    report["scenario_results"][-1]["scenario_id"] = "unknown_scenario"

    with pytest.raises(evaluation.EvaluationReportError):
        evaluation.validate_evaluation_report(report)


def test_pass_report_rejects_failed_hard_gate(tmp_path: Path) -> None:
    report = evaluation.build_report(
        evaluation_id=evaluation.EVALUATION_ID,
        evaluation_base_commit="unit-test-base",
        tmp_dir=tmp_path,
    )
    changed = deepcopy(report)
    changed["hard_gate_results"]["candidate_integrity_passed"]["passed"] = False

    with pytest.raises(evaluation.EvaluationReportError):
        evaluation.validate_evaluation_report(changed)


def test_fail_report_cannot_be_upgraded_manually(tmp_path: Path) -> None:
    report = evaluation.build_report(
        evaluation_id=evaluation.EVALUATION_ID,
        evaluation_base_commit="unit-test-base",
        tmp_dir=tmp_path,
    )
    report["decision"] = evaluation.FAIL_DECISION

    with pytest.raises(evaluation.EvaluationReportError):
        evaluation.validate_evaluation_report(report)
