from knowledge_source_registry_test_helpers import RESOURCE_LIMITS, read_json, read_text


def test_source_registry_budget_document_and_examples_match_limits():
    text = read_text("docs/knowledge-intelligence/source-provenance-registry-resource-budgets.md")
    payload = read_json("examples/knowledge-intelligence/source-registry-resource-budget.json")
    assert payload["resource_limits"] == RESOURCE_LIMITS
    for key, value in RESOURCE_LIMITS.items():
        assert key in text
        assert payload["resource_limits"][key] == value
    assert payload["resource_limits"]["maximum_persisted_source_body_bytes"] == 0
    assert payload["resource_limits"]["maximum_network_calls"] == 0
    assert payload["resource_limits"]["maximum_claim_verifications"] == 0
    assert payload["resource_limits"]["maximum_knowledge_promotions"] == 0
    assert payload["resource_limits"]["maximum_belief_mutations"] == 0
