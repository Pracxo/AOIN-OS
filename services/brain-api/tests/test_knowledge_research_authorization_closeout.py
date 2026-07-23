from knowledge_source_registry_test_helpers import (
    CLOSED_AUTH_ID,
    DECISION,
    SOURCE_AUTH_ID,
    active_source_record,
    closed_research_record,
    read_json,
    validate_source_authorization,
)


def test_aion_204_authorization_is_closed_and_non_reusable():
    closed = closed_research_record()
    assert closed["authorization_transaction_id"] == CLOSED_AUTH_ID
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_consumed_by_task"] == "AION-205"
    assert closed["authorization_consumed_by_prs"] == [116, 117]
    assert closed["authorization_closed_by_task"] == "AION-206"
    assert closed["authorization_closeout_decision"] == DECISION
    assert closed["authorization_expired"] is True
    assert closed["authorization_reusable"] is False


def test_aion_206_creates_single_active_source_registry_authorization():
    program = read_json("docs/knowledge-intelligence/program-ledger.json")
    auth = read_json("docs/knowledge-intelligence/authorization-ledger.json")
    assert program["program_state"] == "source_provenance_registry_authorized_not_implemented"
    assert program["active_knowledge_implementation_authorization"] == SOURCE_AUTH_ID
    assert program["active_knowledge_implementation_task"] == "AION-207"
    assert program["formal_closeout_task"] == "AION-208"
    assert auth["active_knowledge_implementation_authorization"] == SOURCE_AUTH_ID
    validate_source_authorization(active_source_record())
