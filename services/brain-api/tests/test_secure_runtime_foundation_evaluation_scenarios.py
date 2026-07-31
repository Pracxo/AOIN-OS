from secure_runtime_aion232_test_helpers import PASS_DECISION, report


def test_evaluation_report_records_exact_pass_and_scenario_set() -> None:
    payload = report()
    assert payload["evaluation_id"] == "AION-SRIPE-001"
    assert payload["evaluation_type"] == "secure_runtime_foundation_operator_evaluation"
    assert payload["decision"] == PASS_DECISION
    assert payload["evaluation_passed"] is True
    assert payload["scenario_count"] == 28
    assert len(payload["scenario_ids"]) == 28
    assert payload["scenario_ids"] == [item["scenario_id"] for item in payload["scenario_results"]]
    assert all(item["passed"] is True for item in payload["scenario_results"])
    assert all(item["passed"] is True for item in payload["hard_gate_results"])
