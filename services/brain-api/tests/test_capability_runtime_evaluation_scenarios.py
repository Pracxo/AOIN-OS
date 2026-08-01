from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import (
    evaluation_module,
    evaluation_report,
)


def test_evaluation_executes_exact_twenty_eight_scenarios():
    module = evaluation_module()
    report = evaluation_report()

    assert tuple(item["scenario_id"] for item in report["scenarios"]) == module.SCENARIO_IDS
    assert len(report["scenarios"]) == 28
    assert all(item["hard_gate"] is True for item in report["scenarios"])
    assert all(item["status"] == "pass" for item in report["scenarios"])
