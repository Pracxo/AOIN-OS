from __future__ import annotations

from test_governed_learning_memory_program_authorization import load_json


def test_rollback_compensation_and_journal_gates_passed() -> None:
    report = load_json(
        "examples/governed-learning-memory/promotion-operator-evaluation-report.json"
    )
    assert report["hard_gate_results"]["rollback_passed"]["passed"] is True
    assert report["hard_gate_results"]["compensation_passed"]["passed"] is True
    assert report["hard_gate_results"]["journal_integrity_passed"]["passed"] is True
    assert report["git_operations"] == 0 and report["source_mutations"] == 0
