from __future__ import annotations

from test_secure_runtime_integration_program_charter import (
    GLM_DECISION,
    PARENT_PROGRAMS,
    load_json,
)


def test_parent_programs_are_complete_with_zero_active_parent_authorizations() -> None:
    cognitive = load_json("docs/cognitive-architecture/program-ledger.json")
    knowledge = load_json("docs/knowledge-intelligence/program-ledger.json")
    glm_program = load_json("docs/governed-learning-memory/program-ledger.json")
    glm_auth = load_json("docs/governed-learning-memory/authorization-ledger.json")
    self_improvement = load_json("docs/self-improvement/program-ledger.json")
    sri = load_json("docs/secure-runtime-integration/program-ledger.json")

    assert sri["parent_completed_programs"] == PARENT_PROGRAMS
    assert cognitive["program_state"] == "cognitive_architecture_program_complete"
    assert cognitive["cognitive_architecture_program_complete"] is True
    assert cognitive["active_cognitive_implementation_authorization_count"] == 0
    assert knowledge["program_state"] == "knowledge_intelligence_program_complete"
    assert knowledge["knowledge_intelligence_program_complete"] is True
    assert knowledge["active_knowledge_implementation_authorization_count"] == 0
    assert glm_program["program_state"] == "governed_learning_memory_program_complete"
    assert glm_program["governed_learning_memory_program_complete"] is True
    assert glm_program["governed_learning_memory_program_evaluation_id"] == "AION-GLMPE-004"
    assert glm_program["governed_learning_memory_program_evaluation_decision"] == GLM_DECISION
    assert glm_program["active_glm_implementation_authorization_count"] == 0
    assert glm_program["active_glm_implementation_authorization"] is None
    assert glm_program["active_glm_implementation_task"] is None
    assert glm_program["next_glm_implementation_authorization"] is None
    assert glm_program["next_glm_implementation_task"] is None
    assert glm_auth["active_authorizations"] == []
    assert self_improvement["program_id"] == "AION-SELF-IMPROVEMENT-001"
    assert self_improvement["active_self_improvement_implementation_authorization"] == "none"
    assert self_improvement["active_implementation_task"] == "none"
    assert sri["active_self_improvement_implementation_authorization_count"] == 0


def test_aion229_final_evidence_is_reconciled_before_sri_authorization() -> None:
    sri = load_json("docs/secure-runtime-integration/program-ledger.json")
    verification = sri["aion_229_verification"]

    assert verification["primary_pr"] == 146
    assert verification["reconciliation_pr"] == 147
    assert verification["harness_commit"] == "1a45937f6fb5a25ffd468a6843f85f1b9a3bd0f1"
    assert verification["closeout_commit"] == "3d718e29f07d260801bbe372c436442e95224d17"
    assert verification["reconciliation_commit"] == "ef8e7d0387734fc0c5fb12e1d35d38b0761bb342"
    assert verification["primary_merge_commit"] == "a6a6d62eb7c04666a206bfadbbcd640e5bdca10a"
    assert verification["reconciliation_merge_commit"] == "9daca65b0a801988db17906611b00dff882aaacd"
    assert verification["ci_result"] == "pass"
    assert verification["evaluation_id"] == "AION-GLMPE-004"
    assert verification["evaluation_decision"] == GLM_DECISION
    assert verification["governed_learning_memory_program_complete"] is True
    assert verification["active_glm_implementation_authorization_count"] == 0
    assert verification["successor_glm_task"] is None
    assert verification["repeat_live_pilot_authorized"] is False
    assert verification["production_runtime_authorized"] is False
    assert verification["v02_release_ready"] is False
