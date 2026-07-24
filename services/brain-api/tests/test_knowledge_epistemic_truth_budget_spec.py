from __future__ import annotations

from knowledge_claim_graph_evaluation_test_helpers import RESOURCE_LIMITS, read_json, read_text


def test_epistemic_truth_budget_document_and_example_match_authorization():
    auth = read_json("examples/knowledge-intelligence/epistemic-truth-authorization.json")
    budget = read_json("examples/knowledge-intelligence/epistemic-resource-budget.json")
    text = read_text("docs/knowledge-intelligence/epistemic-resource-budgets.md")
    assert auth["resource_limits"] == RESOURCE_LIMITS
    assert budget["resource_limits"] == RESOURCE_LIMITS
    for key, value in RESOURCE_LIMITS.items():
        assert key in text
        assert budget["resource_limits"][key] == value
    for key in (
        "maximum_persistent_assessment_write_batch",
        "maximum_source_body_bytes",
        "maximum_automatic_claim_extractions",
        "maximum_absolute_truth_decisions",
        "maximum_knowledge_promotions",
        "maximum_belief_mutations",
        "maximum_network_calls",
    ):
        assert auth["resource_limits"][key] == 0
