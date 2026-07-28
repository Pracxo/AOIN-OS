from __future__ import annotations

from test_governed_learning_memory_program_authorization import load_json


def test_duplicate_and_conflict_preservation_gates_passed() -> None:
    report = load_json(
        "examples/governed-learning-memory/promotion-operator-evaluation-report.json"
    )
    assert report["hard_gate_results"]["duplicate_detection_passed"]["passed"] is True
    assert report["hard_gate_results"]["conflict_preservation_passed"]["passed"] is True
    assert {
        "exact_duplicate_idempotent_no_op",
        "direct_support_refutation_conflict",
        "temporal_jurisdiction_and_version_conflicts",
        "retraction_and_supersession_conflicts",
    } <= {x["scenario_id"] for x in report["scenario_results"]}
