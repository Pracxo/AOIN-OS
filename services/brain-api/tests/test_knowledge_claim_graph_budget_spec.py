from __future__ import annotations

from knowledge_source_registry_test_helpers import (
    claim_graph_authorization_record,
    read_json,
    read_text,
)

EXPECTED_LIMITS = {
    "maximum_claim_nodes_per_graph": 1000,
    "maximum_evidence_bindings_per_graph": 5000,
    "maximum_claim_relation_edges_per_graph": 5000,
    "maximum_source_registry_references_per_claim": 50,
    "maximum_citation_references_per_claim": 50,
    "maximum_lineage_groups_per_claim": 20,
    "maximum_jurisdictions_per_claim": 20,
    "maximum_versions_per_claim": 20,
    "maximum_temporal_intervals_per_claim": 8,
    "maximum_relation_edges_per_claim": 100,
    "maximum_query_results": 1000,
    "maximum_fixture_records": 2000,
    "maximum_fixture_bytes": 2097152,
    "maximum_concurrent_readers": 4,
    "maximum_concurrent_projections": 4,
    "maximum_graph_write_batch": 0,
    "maximum_source_body_bytes": 0,
    "maximum_automatic_claim_extractions": 0,
    "maximum_claim_verifications": 0,
    "maximum_truth_decisions": 0,
    "maximum_confidence_calculations": 0,
    "maximum_knowledge_promotions": 0,
    "maximum_belief_mutations": 0,
    "maximum_network_calls": 0,
    "maximum_search_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_approvals_created": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}


def test_claim_graph_budget_document_and_examples_match_authorization():
    record = claim_graph_authorization_record()
    budget = read_json("examples/knowledge-intelligence/claim-graph-resource-budget.json")
    text = read_text(
        "docs/knowledge-intelligence/temporal-claim-evidence-graph-resource-budgets.md"
    )
    assert record["resource_limits"] == EXPECTED_LIMITS
    assert budget["resource_limits"] == EXPECTED_LIMITS
    for key, value in EXPECTED_LIMITS.items():
        assert key in text
        assert budget["resource_limits"][key] == value
    assert record["resource_limits"]["maximum_graph_write_batch"] == 0
    assert record["resource_limits"]["maximum_claim_verifications"] == 0
    assert record["resource_limits"]["maximum_truth_decisions"] == 0
    assert record["resource_limits"]["maximum_confidence_calculations"] == 0
    assert record["resource_limits"]["maximum_knowledge_promotions"] == 0
    assert record["resource_limits"]["maximum_belief_mutations"] == 0
