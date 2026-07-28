from __future__ import annotations

import pytest
from scripts.lib import governed_learning_memory_promotion_operator_evaluation as evaluation
from test_governed_learning_memory_program_authorization import load_json


def test_report_rejects_missing_hard_gate() -> None:
    report = load_json(
        "examples/governed-learning-memory/promotion-operator-evaluation-report.json"
    )
    report["hard_gate_results"].pop("approval_binding_passed")
    with pytest.raises(evaluation.EvaluationReportError):
        evaluation.validate_evaluation_report(report)


def test_approval_closeout_is_not_persistence_approval() -> None:
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json")
    closed = next(
        x for x in auth["records"] if x["authorization_transaction_id"] == "AION-221-GLM-0001"
    )
    new = next(
        x for x in auth["records"] if x["authorization_transaction_id"] == "AION-223-GLM-0002"
    )
    assert (
        closed["evaluation_used_as_persistence_approval"] is False
        and closed["evaluation_reusable"] is False
    )
    assert (
        new["approval_policy"]["minimum_independent_approvers"] == 2
        and new["approval_policy"]["plan_approval_can_authorize_persistence"] is False
    )
