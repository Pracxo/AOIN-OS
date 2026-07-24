from __future__ import annotations

from knowledge_source_registry_test_helpers import active_knowledge_authorization_record, read_json

SCOPE = (
    "append-only-immutable-temporal-claim-evidence-provenance-jurisdiction-"
    "version-contradiction-graph-core"
)
DECISION = (
    "SOURCE_PROVENANCE_REGISTRY_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "TEMPORAL_CLAIM_EVIDENCE_GRAPH_AUTHORIZATION"
)


def test_claim_graph_authorization_exact_lifecycle_and_parentage():
    program = read_json("docs/knowledge-intelligence/program-ledger.json")
    record = active_knowledge_authorization_record()
    assert program["program_state"] in {
        "temporal_claim_evidence_graph_authorized_not_implemented",
        "temporal_claim_evidence_graph_implemented_write_disabled_pending_closeout",
    }
    assert record["authorization_transaction_id"] == "AION-208-KI-0003"
    assert record["approval_record_id"] == "AION-208-KI-0003"
    assert record["parent_authorization_transaction_id"] == "AION-206-KI-0002"
    assert record["parent_evaluation_id"] == "AION-SPRE-001"
    assert record["parent_evaluation_decision"] == DECISION
    assert record["parent_closeout_task"] == "AION-208"
    assert record["parent_registry_implementation_task"] == "AION-207"
    assert record["parent_registry_implementation_prs"] == [119]
    assert record["implementation_task"] == "AION-209"
    assert record["formal_closeout_task"] == "AION-210"
    assert record["authorization_scope"] == SCOPE
    assert record["authorization_active"] is True
    assert record["authorization_consumed"] is False
    assert record["authorization_expired"] is False
    assert record["authorization_reusable"] is False
    if program["program_state"].startswith("temporal_claim_evidence_graph_implemented"):
        assert program["temporal_claim_evidence_graph_implemented"] is True
        assert program["persistent_claim_graph_write_enabled"] is False
        assert program["claim_graph_runtime_enabled"] is False
        assert record["temporal_claim_evidence_graph_implemented"] is True
        assert record["persistent_claim_graph_write_enabled"] is False
        assert record["claim_graph_runtime_enabled"] is False


def test_claim_graph_authorization_capability_maps_are_strict():
    record = active_knowledge_authorization_record()
    assert len(record["authorized_capabilities"]) >= 59
    assert all(record["authorized_capabilities"].values())
    assert len(record["prohibited_capabilities"]) >= 45
    assert all(value is False for value in record["prohibited_capabilities"].values())
    assert record["prohibited_capabilities"]["claim_verification_enabled"] is False
    assert record["prohibited_capabilities"]["truth_decision_enabled"] is False
    assert record["prohibited_capabilities"]["epistemic_confidence_enabled"] is False
    assert record["prohibited_capabilities"]["knowledge_promotion_enabled"] is False
    assert record["prohibited_capabilities"]["cognitive_belief_mutation_enabled"] is False
    assert record["prohibited_capabilities"]["persistent_claim_graph_write_enabled"] is False
    assert record["prohibited_capabilities"]["network_acquisition_enabled"] is False
