from __future__ import annotations

from test_governed_learning_memory_program_authorization import KI_DECISION, load_json


def test_parent_program_lineage_is_preserved_without_reactivation() -> None:
    glm = load_json("docs/governed-learning-memory/program-ledger.json")
    ki_program = load_json("docs/knowledge-intelligence/program-ledger.json")
    ki_auth = load_json("docs/knowledge-intelligence/authorization-ledger.json")
    cognitive = load_json("docs/cognitive-architecture/program-ledger.json")
    self_improvement = load_json("docs/self-improvement/program-ledger.json")

    assert glm["parent_program_state"]["knowledge_intelligence"]["program_state"] == (
        "knowledge_intelligence_program_complete"
    )
    assert glm["parent_program_state"]["knowledge_intelligence"]["decision"] == KI_DECISION
    assert (
        glm["parent_program_state"]["knowledge_intelligence"]["successor_created_by_aion_220"]
        is False
    )
    assert ki_program["program_state"] == "knowledge_intelligence_program_complete"
    assert ki_auth["active_knowledge_implementation_authorization_count"] == 0
    assert not any(item.get("authorization_active") is True for item in ki_auth["records"])

    assert cognitive["program_state"] == "cognitive_architecture_program_complete"
    assert cognitive["active_cognitive_implementation_authorization_count"] == 0
    assert self_improvement["active_self_improvement_implementation_authorization"] == "none"
    assert self_improvement["active_implementation_task"] == "none"
