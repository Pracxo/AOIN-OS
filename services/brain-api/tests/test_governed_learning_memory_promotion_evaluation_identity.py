from __future__ import annotations

from test_governed_learning_memory_program_authorization import load_json


def test_identity_and_transaction_binding_hard_gates_passed() -> None:
    report = load_json(
        "examples/governed-learning-memory/promotion-operator-evaluation-report.json"
    )
    gates = report["hard_gate_results"]
    assert gates["identity_derivation_passed"]["passed"] is True
    assert gates["approval_binding_passed"]["passed"] is True
    assert gates["determinism_passed"]["passed"] is True
    assert "deterministic_knowledge_identity" in {
        x["scenario_id"] for x in report["scenario_results"]
    }
