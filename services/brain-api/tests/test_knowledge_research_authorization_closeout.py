from knowledge_source_registry_test_helpers import (
    CLAIM_GRAPH_AUTH_ID,
    CLOSED_AUTH_ID,
    DECISION,
    DOMAIN_EXPERT_MESH_AUTH_ID,
    EPISTEMIC_AUTH_ID,
    SOURCE_AUTH_ID,
    TOOL_VERIFICATION_AUTH_ID,
    active_source_record,
    closed_research_record,
    read_json,
    validate_source_authorization,
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
AION219_STATE = "controlled_public_research_pilot_authorized_not_implemented"


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
    assert program["program_state"] in {
        "source_provenance_registry_implemented_write_disabled_pending_closeout",
        "temporal_claim_evidence_graph_authorized_not_implemented",
        "temporal_claim_evidence_graph_implemented_write_disabled_pending_closeout",
        "epistemic_truth_engine_authorized_not_implemented",
        AION211_STATE,
        AION213_STATE,
        AION213_IMPLEMENTED_STATE,
        AION215_STATE,
        AION215_IMPLEMENTED_STATE,
        AION217_STATE,
        AION217_IMPLEMENTED_STATE,
        AION219_STATE,
    }
    if program["program_state"] in {
        "epistemic_truth_engine_authorized_not_implemented",
        AION211_STATE,
    }:
        assert program["active_knowledge_implementation_authorization"] == EPISTEMIC_AUTH_ID
        assert program["active_knowledge_implementation_task"] == "AION-211"
        assert program["formal_closeout_task"] == "AION-212"
        if program["program_state"] == AION211_STATE:
            assert program["epistemic_truth_engine_implemented"] is True
            assert program["epistemic_truth_engine_runtime_enabled"] is False
            assert program["persistent_assessment_write_enabled"] is False
    elif program["program_state"] in {AION213_STATE, AION213_IMPLEMENTED_STATE}:
        assert program["active_knowledge_implementation_authorization"] == (
            DOMAIN_EXPERT_MESH_AUTH_ID
        )
        assert program["active_knowledge_implementation_task"] == "AION-213"
        assert program["formal_closeout_task"] == "AION-214"
        assert program["epistemic_truth_engine_implemented"] is True
        assert program["epistemic_truth_engine_runtime_enabled"] is False
        assert program["persistent_assessment_write_enabled"] is False
        if program["program_state"] == AION213_IMPLEMENTED_STATE:
            assert program["domain_expert_mesh_implemented"] is True
            assert program["model_call_enabled"] is False
            assert program["persistent_mesh_write_enabled"] is False
    elif program["program_state"] == AION219_STATE:
        assert program["active_knowledge_implementation_authorization"] == (
            "AION-218-KI-0008"
        )
        assert program["active_knowledge_implementation_task"] == "AION-219"
        assert program["formal_closeout_task"] == "AION-220"
        assert program["epistemic_truth_engine_implemented"] is True
        assert program["epistemic_truth_engine_runtime_enabled"] is False
        assert program["persistent_assessment_write_enabled"] is False
        assert program["domain_expert_mesh_implemented"] is True
        assert program["model_call_enabled"] is False
        assert program["persistent_mesh_write_enabled"] is False
        assert program["tool_verification_fabric_authorized"] is True
        assert program["tool_verification_fabric_implemented"] is True
        assert program["tool_verification_fabric_runtime_enabled"] is False
        assert program["verified_knowledge_memory_authorized"] is True
        assert program["verified_knowledge_memory_implemented"] is True
        assert program["persistent_verified_knowledge_write_enabled"] is False
        assert program["actual_tool_execution_enabled"] is False
        assert program["controlled_public_research_pilot_authorized"] is True
        assert program["controlled_public_research_pilot_implemented"] is False
        assert program["public_network_fetch_enabled"] is False
    elif program["program_state"] in {AION217_STATE, AION217_IMPLEMENTED_STATE}:
        assert program["active_knowledge_implementation_authorization"] == (
            "AION-216-KI-0007"
        )
        assert program["active_knowledge_implementation_task"] == "AION-217"
        assert program["formal_closeout_task"] == "AION-218"
        assert program["epistemic_truth_engine_implemented"] is True
        assert program["epistemic_truth_engine_runtime_enabled"] is False
        assert program["persistent_assessment_write_enabled"] is False
        assert program["domain_expert_mesh_implemented"] is True
        assert program["model_call_enabled"] is False
        assert program["persistent_mesh_write_enabled"] is False
        assert program["tool_verification_fabric_authorized"] is True
        assert program["tool_verification_fabric_implemented"] is True
        assert program["tool_verification_fabric_runtime_enabled"] is False
        assert program["verified_knowledge_memory_authorized"] is True
        assert program["verified_knowledge_memory_implemented"] is (
            program["program_state"] == AION217_IMPLEMENTED_STATE
        )
        assert program["persistent_verified_knowledge_write_enabled"] is False
        assert program["actual_tool_execution_enabled"] is False
    elif program["program_state"] in {AION215_STATE, AION215_IMPLEMENTED_STATE}:
        assert program["active_knowledge_implementation_authorization"] == (
            TOOL_VERIFICATION_AUTH_ID
        )
        assert program["active_knowledge_implementation_task"] == "AION-215"
        assert program["formal_closeout_task"] == "AION-216"
        assert program["epistemic_truth_engine_implemented"] is True
        assert program["epistemic_truth_engine_runtime_enabled"] is False
        assert program["persistent_assessment_write_enabled"] is False
        assert program["domain_expert_mesh_implemented"] is True
        assert program["model_call_enabled"] is False
        assert program["persistent_mesh_write_enabled"] is False
        assert program["tool_verification_fabric_authorized"] is True
        assert program["tool_verification_fabric_implemented"] is (
            program["program_state"] == AION215_IMPLEMENTED_STATE
        )
        if program["program_state"] == AION215_IMPLEMENTED_STATE:
            assert program["tool_verification_fabric_state"] == (
                "implemented_deterministic_simulation_verification_attestation_persistent_write_disabled"
            )
            assert program["tool_verification_fabric_runtime_enabled"] is False
        assert program["actual_tool_execution_enabled"] is False
    elif program["program_state"] in {
        "temporal_claim_evidence_graph_authorized_not_implemented",
        "temporal_claim_evidence_graph_implemented_write_disabled_pending_closeout",
    }:
        assert program["active_knowledge_implementation_authorization"] == CLAIM_GRAPH_AUTH_ID
        assert program["active_knowledge_implementation_task"] == "AION-209"
        assert program["formal_closeout_task"] == "AION-210"
    else:
        assert program["active_knowledge_implementation_authorization"] == SOURCE_AUTH_ID
        assert program["active_knowledge_implementation_task"] == "AION-207"
        assert program["formal_closeout_task"] == "AION-208"
    assert program["source_provenance_registry_implemented"] is True
    assert (
        program["source_provenance_registry_state"]
        == "implemented_append_only_in_memory_replay_persistent_write_disabled"
    )
    assert auth["active_knowledge_implementation_authorization"] in {
        SOURCE_AUTH_ID,
        CLAIM_GRAPH_AUTH_ID,
        EPISTEMIC_AUTH_ID,
        DOMAIN_EXPERT_MESH_AUTH_ID,
        TOOL_VERIFICATION_AUTH_ID,
        "AION-216-KI-0007",
        "AION-218-KI-0008",
    }
    validate_source_authorization(active_source_record())
