from __future__ import annotations

from knowledge_source_registry_test_helpers import (
    CLAIM_GRAPH_AUTH_ID,
    EPISTEMIC_AUTH_ID,
    SOURCE_AUTH_ID,
    active_knowledge_authorization_record,
    read_json,
    source_authorization_record,
    validate_source_authorization,
)

DECISION = (
    "SOURCE_PROVENANCE_REGISTRY_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "TEMPORAL_CLAIM_EVIDENCE_GRAPH_AUTHORIZATION"
)


def test_aion_206_source_registry_authorization_is_closed_and_non_reusable():
    record = source_authorization_record()
    validate_source_authorization(record)
    assert record["authorization_transaction_id"] == SOURCE_AUTH_ID
    assert record["authorization_active"] is False
    assert record["authorization_consumed"] is True
    assert record["authorization_consumed_by_task"] == "AION-207"
    assert record["authorization_consumed_by_prs"] == [119]
    assert record["authorization_consumed_by_feature_commits"] == [
        "3e95d788726be4d3f51f299aa005df87aa00375b"
    ]
    assert record["authorization_consumed_by_merge_commits"] == [
        "14c12bebfced7fd6345c8af2899988aadfa91a44"
    ]
    assert record["authorization_expired"] is True
    assert record["authorization_reusable"] is False
    assert record["authorization_closed_by_task"] == "AION-208"
    assert record["source_registry_operator_evaluation_id"] == "AION-SPRE-001"
    assert record["source_registry_operator_evaluation_decision"] == DECISION


def test_aion_208_claim_graph_authorization_hands_off_to_next_active_authorization():
    program = read_json("docs/knowledge-intelligence/program-ledger.json")
    auth = read_json("docs/knowledge-intelligence/authorization-ledger.json")
    active = active_knowledge_authorization_record()
    assert auth["active_cognitive_implementation_authorization_count"] == 0
    assert auth["active_knowledge_implementation_authorization_count"] == 1
    assert program["active_knowledge_implementation_authorization_count"] == 1
    if program["program_state"] == "epistemic_truth_engine_authorized_not_implemented":
        assert active["authorization_transaction_id"] == EPISTEMIC_AUTH_ID
        assert active["implementation_task"] == "AION-211"
        assert active["formal_closeout_task"] == "AION-212"
    else:
        assert active["authorization_transaction_id"] == CLAIM_GRAPH_AUTH_ID
        assert active["implementation_task"] == "AION-209"
        assert active["formal_closeout_task"] == "AION-210"
    assert active["authorization_active"] is True
    assert active["authorization_consumed"] is False
    assert active["authorization_expired"] is False
    assert active["authorization_reusable"] is False
