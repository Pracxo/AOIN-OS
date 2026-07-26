from __future__ import annotations

from knowledge_source_registry_test_helpers import (
    CLAIM_GRAPH_AUTH_ID,
    DOMAIN_EXPERT_MESH_AUTH_ID,
    EPISTEMIC_AUTH_ID,
    SOURCE_AUTH_ID,
    TOOL_VERIFICATION_AUTH_ID,
    active_knowledge_authorization_record,
    read_json,
    source_authorization_record,
    validate_source_authorization,
)

DECISION = (
    "SOURCE_PROVENANCE_REGISTRY_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "TEMPORAL_CLAIM_EVIDENCE_GRAPH_AUTHORIZATION"
)
AION211_STATE = (
    "epistemic_truth_engine_implemented_persistent_write_disabled_pending_closeout"
)
AION213_STATE = "domain_expert_mesh_authorized_not_implemented"
AION213_IMPLEMENTED_STATE = (
    "domain_expert_mesh_implemented_persistent_write_disabled_pending_closeout"
)
AION215_STATE = "tool_verification_fabric_authorized_not_implemented"
AION215_IMPLEMENTED_STATE = (
    "tool_verification_fabric_implemented_persistent_write_disabled_pending_closeout"
)
AION217_STATE = "verified_knowledge_memory_authorized_not_implemented"
AION217_IMPLEMENTED_STATE = (
    "verified_knowledge_memory_implemented_persistent_write_disabled_pending_closeout"
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
    if program["program_state"] in {
        "epistemic_truth_engine_authorized_not_implemented",
        AION211_STATE,
    }:
        assert active["authorization_transaction_id"] == EPISTEMIC_AUTH_ID
        assert active["implementation_task"] == "AION-211"
        assert active["formal_closeout_task"] == "AION-212"
        if program["program_state"] == AION211_STATE:
            assert active["epistemic_truth_engine_implemented"] is True
            assert active["epistemic_truth_engine_runtime_enabled"] is False
            assert active["resource_limits"]["maximum_persistent_assessment_write_batch"] == 0
    elif program["program_state"] in {AION213_STATE, AION213_IMPLEMENTED_STATE}:
        assert active["authorization_transaction_id"] == DOMAIN_EXPERT_MESH_AUTH_ID
        assert active["implementation_task"] == "AION-213"
        assert active["formal_closeout_task"] == "AION-214"
        assert active["domain_expert_mesh_authorized"] is True
        assert active["domain_expert_mesh_implemented"] is False
        assert active["runtime_effect"] is False
        if program["program_state"] == AION213_IMPLEMENTED_STATE:
            assert program["domain_expert_mesh_implemented"] is True
            assert program["model_call_enabled"] is False
            assert program["persistent_mesh_write_enabled"] is False
    elif program["program_state"] in {AION217_STATE, AION217_IMPLEMENTED_STATE}:
        assert active["authorization_transaction_id"] == "AION-216-KI-0007"
        assert active["implementation_task"] == "AION-217"
        assert active["formal_closeout_task"] == "AION-218"
        assert active["verified_knowledge_memory_authorized"] is True
        assert active["verified_knowledge_memory_implemented"] is (
            program["program_state"] == AION217_IMPLEMENTED_STATE
        )
        assert active["runtime_effect"] is False
        assert active["persistent_verified_knowledge_write_enabled"] is False
    elif program["program_state"] in {AION215_STATE, AION215_IMPLEMENTED_STATE}:
        assert active["authorization_transaction_id"] == TOOL_VERIFICATION_AUTH_ID
        assert active["implementation_task"] == "AION-215"
        assert active["formal_closeout_task"] == "AION-216"
        assert active["tool_verification_fabric_authorized"] is True
        assert active["tool_verification_fabric_implemented"] is (
            program["program_state"] == AION215_IMPLEMENTED_STATE
        )
        assert active["runtime_effect"] is False
        assert active["actual_tool_execution_enabled"] is False
        if program["program_state"] == AION215_IMPLEMENTED_STATE:
            assert active["tool_verification_fabric_state"] == (
                "implemented_deterministic_simulation_verification_attestation_persistent_write_disabled"
            )
            assert active["tool_verification_fabric_runtime_enabled"] is False
    else:
        assert active["authorization_transaction_id"] == CLAIM_GRAPH_AUTH_ID
        assert active["implementation_task"] == "AION-209"
        assert active["formal_closeout_task"] == "AION-210"
    assert active["authorization_active"] is True
    assert active["authorization_consumed"] is False
    assert active["authorization_expired"] is False
    assert active["authorization_reusable"] is False
