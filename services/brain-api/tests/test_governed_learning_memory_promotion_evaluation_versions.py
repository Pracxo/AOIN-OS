from __future__ import annotations

from test_governed_learning_memory_program_authorization import load_json


def test_version_planning_gates_passed_without_persistence() -> None:
    report = load_json(
        "examples/governed-learning-memory/promotion-operator-evaluation-report.json"
    )
    summary = load_json("examples/governed-learning-memory/persistent-knowledge-version.json")
    assert report["hard_gate_results"]["version_planning_passed"]["passed"] is True
    assert (
        report["persistent_knowledge_writes"] == 0
        and report["persistent_verified_knowledge_writes"] == 0
    )
    assert (
        summary["persistent_record_created_by_aion_223"] is False
        and summary["active_projection_marker_is_append_only_event"] is True
    )
