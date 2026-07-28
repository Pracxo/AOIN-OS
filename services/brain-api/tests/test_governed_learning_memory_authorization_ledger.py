from __future__ import annotations

from test_governed_learning_memory_program_authorization import (
    AUTH_ID,
    CANDIDATE_ID,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    KI_DECISION,
    SCOPE,
    WORKSTREAM,
    load_json,
)


def test_authorization_ledger_has_single_active_aion_222_authorization() -> None:
    ledger = load_json("docs/governed-learning-memory/authorization-ledger.json")

    assert ledger["active_authorizations"] == [AUTH_ID]
    assert len(ledger["records"]) == 1
    record = ledger["records"][0]
    assert record["authorization_transaction_id"] == AUTH_ID
    assert record["approval_record_id"] == AUTH_ID
    assert record["candidate_id"] == CANDIDATE_ID
    assert record["workstream"] == WORKSTREAM
    assert record["implementation_task"] == IMPLEMENTATION_TASK
    assert record["formal_closeout_task"] == FORMAL_CLOSEOUT_TASK
    assert record["authorization_scope"] == SCOPE
    assert record["authorization_active"] is True
    assert record["authorization_consumed"] is False
    assert record["authorization_expired"] is False
    assert record["authorization_reusable"] is False
    assert record["parent_knowledge_program_closeout_task"] == "AION-220"
    assert record["parent_knowledge_program_evaluation_id"] == "AION-KIPE-001"
    assert record["parent_knowledge_program_decision"] == KI_DECISION
