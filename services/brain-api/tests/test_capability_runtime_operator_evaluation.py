from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import (
    evaluation_module,
    evaluation_report,
)


def test_operator_evaluation_report_passes_exact_decision():
    module = evaluation_module()
    report = evaluation_report()

    assert report["evaluation_id"] == module.EVALUATION_ID
    assert report["decision"] == module.PASS_DECISION
    assert report["authorization_transaction_id"] == module.AUTHORIZATION_ID
    assert all(report["hard_gates"].values())


def test_operator_evaluation_report_fingerprint_validates():
    module = evaluation_module()

    module.validate_report(evaluation_report())
