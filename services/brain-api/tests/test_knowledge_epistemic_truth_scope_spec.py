from __future__ import annotations

from knowledge_claim_graph_evaluation_test_helpers import read_json, read_text


def test_epistemic_truth_scope_requires_evidence_assessment_not_truth_oracle():
    auth = read_json("examples/knowledge-intelligence/epistemic-truth-authorization.json")
    text = read_text("docs/knowledge-intelligence/epistemic-truth-engine-boundary.md")
    required = [
        "source_independence_counting_approved",
        "duplicate_evidence_suppression_approved",
        "temporal_freshness_evaluation_approved",
        "jurisdiction_applicability_evaluation_approved",
        "version_applicability_evaluation_approved",
        "correction_relation_evaluation_approved",
        "retraction_relation_evaluation_approved",
        "supersession_relation_evaluation_approved",
        "explicit_abstention_approved",
    ]
    for key in required:
        assert auth["authorized_capabilities"][key] is True
    assert auth["prohibited_capabilities"]["absolute_truth_oracle_enabled"] is False
    assert auth["prohibited_capabilities"]["automatic_claim_acceptance_enabled"] is False
    assert "not claim metaphysical certainty" in text
