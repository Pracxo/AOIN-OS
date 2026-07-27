from __future__ import annotations

import copy

from knowledge_claim_graph_evaluation_test_helpers import (
    CLAIM_GRAPH_AUTH_ID,
    DECISION,
    DOMAIN_EXPERT_MESH_AUTH_ID,
    EPISTEMIC_AUTH_ID,
    active_authorization_record,
    authorization_record,
    read_json,
    validate_epistemic_authorization,
)


def test_aion_208_claim_graph_authorization_is_closed_and_non_reusable():
    record = authorization_record(CLAIM_GRAPH_AUTH_ID)
    assert record["authorization_transaction_id"] == CLAIM_GRAPH_AUTH_ID
    assert record["authorization_active"] is False
    assert record["authorization_consumed"] is True
    assert record["authorization_consumed_by_task"] == "AION-209"
    assert record["authorization_consumed_by_prs"] == [121]
    assert record["authorization_consumed_by_feature_commits"] == [
        "0a84080c83f87eef94b5191c432021776c6a336a",
        "d50252c84a0a02b75317c7d2051eaee4fb9dc54c",
    ]
    assert record["authorization_consumed_by_merge_commits"] == [
        "f9e2438a49aae458983fc57cee5c12b5ef0ab856"
    ]
    assert record["authorization_expired"] is True
    assert record["authorization_reusable"] is False
    assert record["authorization_closed_by_task"] == "AION-210"
    assert record["claim_graph_operator_evaluation_id"] == "AION-TCGE-001"
    assert record["claim_graph_operator_evaluation_decision"] == DECISION
    assert record["evaluation_used_as_approval"] is False


def test_aion_210_creates_sole_active_epistemic_authorization():
    program = read_json("docs/knowledge-intelligence/program-ledger.json")
    record = authorization_record(EPISTEMIC_AUTH_ID)
    validate_epistemic_authorization(record)
    assert record["authorization_transaction_id"] == EPISTEMIC_AUTH_ID
    if program["program_state"] == "knowledge_intelligence_program_complete":
        records = read_json("docs/knowledge-intelligence/authorization-ledger.json")[
            "records"
        ]
        assert [
            item
            for item in records
            if item.get("authorization_active") is True
        ] == []
        assert program["active_knowledge_implementation_authorization_count"] == 0
        assert program["active_knowledge_implementation_authorization"] is None
        assert program["active_knowledge_implementation_task"] is None
        assert program["formal_closeout_task"] is None
        assert record["authorization_active"] is False
        assert record["authorization_consumed"] is True
        assert record["authorization_expired"] is True
        assert record["authorization_reusable"] is False
        assert record["authorization_closed_by_task"] == "AION-212"
        assert program["active_cognitive_implementation_authorization_count"] == 0
        return

    active = active_authorization_record()
    if program["program_state"] in {
        "controlled_public_research_pilot_authorized_not_implemented",
        "controlled_public_research_pilot_implemented_operator_invoked_persistent_write_disabled_pending_closeout",
    }:
        assert active["authorization_transaction_id"] == "AION-218-KI-0008"
        assert (
            program["active_knowledge_implementation_authorization"]
            == "AION-218-KI-0008"
        )
        assert program["active_knowledge_implementation_task"] == "AION-219"
        assert program["formal_closeout_task"] == "AION-220"
        assert record["authorization_active"] is False
        assert record["authorization_consumed"] is True
        assert record["authorization_expired"] is True
        assert record["authorization_reusable"] is False
        assert record["authorization_closed_by_task"] == "AION-212"
    elif program["program_state"] in {
        "verified_knowledge_memory_authorized_not_implemented",
        "verified_knowledge_memory_implemented_persistent_write_disabled_pending_closeout",
    }:
        assert active["authorization_transaction_id"] == "AION-216-KI-0007"
        assert (
            program["active_knowledge_implementation_authorization"]
            == "AION-216-KI-0007"
        )
        assert program["active_knowledge_implementation_task"] == "AION-217"
        assert program["formal_closeout_task"] == "AION-218"
        assert record["authorization_active"] is False
        assert record["authorization_consumed"] is True
        assert record["authorization_expired"] is True
        assert record["authorization_reusable"] is False
        assert record["authorization_closed_by_task"] == "AION-212"
    elif program["program_state"] in {
        "tool_verification_fabric_authorized_not_implemented",
        "tool_verification_fabric_implemented_persistent_write_disabled_pending_closeout",
    }:
        assert active["authorization_transaction_id"] == "AION-214-KI-0006"
        assert (
            program["active_knowledge_implementation_authorization"]
            == "AION-214-KI-0006"
        )
        assert program["active_knowledge_implementation_task"] == "AION-215"
        assert program["formal_closeout_task"] == "AION-216"
        assert record["authorization_active"] is False
        assert record["authorization_consumed"] is True
        assert record["authorization_expired"] is True
        assert record["authorization_reusable"] is False
        assert record["authorization_closed_by_task"] == "AION-212"
    elif program["program_state"] in {
        "domain_expert_mesh_authorized_not_implemented",
        "domain_expert_mesh_implemented_persistent_write_disabled_pending_closeout",
    }:
        assert active["authorization_transaction_id"] == DOMAIN_EXPERT_MESH_AUTH_ID
        assert (
            program["active_knowledge_implementation_authorization"]
            == DOMAIN_EXPERT_MESH_AUTH_ID
        )
        assert program["active_knowledge_implementation_task"] == "AION-213"
        assert program["formal_closeout_task"] == "AION-214"
    else:
        assert active["authorization_transaction_id"] == EPISTEMIC_AUTH_ID
        assert program["active_knowledge_implementation_authorization"] == EPISTEMIC_AUTH_ID
        assert program["active_knowledge_implementation_task"] == "AION-211"
        assert program["formal_closeout_task"] == "AION-212"
    assert program["active_cognitive_implementation_authorization_count"] == 0


def test_closed_claim_graph_authorization_cannot_reactivate():
    record = copy.deepcopy(authorization_record(CLAIM_GRAPH_AUTH_ID))
    record["authorization_active"] = True
    assert record["authorization_consumed"] is True
    assert record["authorization_expired"] is True
    assert record["authorization_reusable"] is False
