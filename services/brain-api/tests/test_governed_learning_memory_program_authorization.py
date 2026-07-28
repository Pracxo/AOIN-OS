from __future__ import annotations

import json
from pathlib import Path

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    AION223_AUTHORIZATION_ID,
    AION224_APPROVED_CAPABILITIES,
    AION224_AUTHORIZATION_SCOPE,
    AION224_PROHIBITED_CAPABILITIES,
    AION224_TASK,
    AION225_TASK,
    PASS_DECISION,
    PROGRAM_ID,
    validate_authorization_ledgers,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
AUTH_ID = AION223_AUTHORIZATION_ID
CANDIDATE_ID = "operator-approved-local-append-only-knowledge-persistence-core"
WORKSTREAM = "governed-learning-memory-local-persistence"
IMPLEMENTATION_TASK = AION224_TASK
FORMAL_CLOSEOUT_TASK = AION225_TASK
SCOPE = AION224_AUTHORIZATION_SCOPE
KI_DECISION = "CONTROLLED_PUBLIC_RESEARCH_PILOT_PASS_COMPLETE_KNOWLEDGE_INTELLIGENCE_PROGRAM"
AUTHORIZED_CAPABILITIES = set(AION224_APPROVED_CAPABILITIES)
PROHIBITED_CAPABILITIES = set(AION224_PROHIBITED_CAPABILITIES)


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_aion_223_program_and_authorization_are_exact() -> None:
    program, auth = validate_authorization_ledgers(REPO_ROOT)
    for payload in (program, auth):
        assert payload["program_id"] == PROGRAM_ID
        assert (
            payload["program_state"]
            == "governed_learning_memory_local_persistence_authorized_not_implemented"
        )
        assert payload["active_glm_implementation_authorization_count"] == 1
        assert payload["active_glm_implementation_authorization"] == AUTH_ID
        assert payload["active_glm_implementation_task"] == IMPLEMENTATION_TASK
        assert payload["formal_closeout_task"] == FORMAL_CLOSEOUT_TASK
        assert payload["promotion_transaction_operator_evaluation_decision"] == PASS_DECISION
    assert auth["authorization_transaction_id"] == AUTH_ID
    assert auth["approval_record_id"] == AUTH_ID
    assert auth["candidate_id"] == CANDIDATE_ID
    assert auth["workstream"] == WORKSTREAM
    assert auth["implementation_task"] == IMPLEMENTATION_TASK
    assert auth["formal_closeout_task"] == FORMAL_CLOSEOUT_TASK
    assert auth["authorization_scope"] == SCOPE
    assert auth["authorization_active"] is True
    assert auth["authorization_consumed"] is False
    assert auth["authorization_expired"] is False
    assert auth["authorization_reusable"] is False


def test_authorized_and_prohibited_capabilities_are_explicit() -> None:
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json")
    assert set(auth["authorized_capabilities"]) == AUTHORIZED_CAPABILITIES
    assert set(auth["prohibited_capabilities"]) == PROHIBITED_CAPABILITIES
    assert all(auth["authorized_capabilities"][k] is True for k in AUTHORIZED_CAPABILITIES)
    assert all(auth["prohibited_capabilities"][k] is False for k in PROHIBITED_CAPABILITIES)
