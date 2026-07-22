from knowledge_intelligence_test_helpers import RESOURCE_LIMITS, read_json, read_text


def test_budget_document_and_example_match_authorization_limits():
    text = read_text("docs/knowledge-intelligence/research-resource-budgets.md")
    payload = read_json("examples/knowledge-intelligence/research-resource-budget.json")
    assert payload["resource_limits"] == RESOURCE_LIMITS
    for key, value in RESOURCE_LIMITS.items():
        assert key in text
        assert payload["resource_limits"][key] == value
    assert payload["resource_limits"]["network_calls_during_AION_204"] == 0
    assert payload["resource_limits"]["research_runtime_enabled"] is False
    assert payload["resource_limits"]["background_crawls"] == 0
    assert payload["resource_limits"]["knowledge_promotions"] == 0
    assert payload["resource_limits"]["cognitive_belief_mutations"] == 0
