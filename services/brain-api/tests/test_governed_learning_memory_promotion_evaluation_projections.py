from __future__ import annotations

from test_governed_learning_memory_program_authorization import load_json


def test_projection_planning_gates_pass_without_memory_or_belief_writes() -> None:
    report = load_json(
        "examples/governed-learning-memory/promotion-operator-evaluation-report.json"
    )
    projection = load_json(
        "examples/governed-learning-memory/persistent-memory-projection-record.json"
    )
    assert report["hard_gate_results"]["projection_planning_passed"]["passed"] is True
    for key in [
        "semantic_memory_writes",
        "episodic_memory_writes",
        "procedural_memory_writes",
        "cognitive_memory_writes",
        "belief_creations",
    ]:
        assert report[key] == 0
    assert (
        projection["production_memory_written"] is False and projection["belief_written"] is False
    )
