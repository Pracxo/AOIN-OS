from __future__ import annotations

from knowledge_claim_graph_evaluation_test_helpers import (
    CAPS,
    CONFIDENCE_BANDS,
    read_json,
    read_text,
)


def test_epistemic_scorecard_statuses_bands_caps_and_abstention():
    scorecard = read_json("examples/knowledge-intelligence/epistemic-scorecard.json")
    statuses = read_json("examples/knowledge-intelligence/epistemic-assessment-status.json")
    assessment = read_json("examples/knowledge-intelligence/epistemic-assessment.json")
    text = read_text("docs/knowledge-intelligence/epistemic-confidence-scorecard.md")
    assert statuses["confidence_bands"] == CONFIDENCE_BANDS
    assert scorecard["hard_caps"] == CAPS
    assert scorecard["model_call_enabled"] is False
    assert scorecard["hidden_weights_enabled"] is False
    assert scorecard["learned_weights_enabled"] is False
    assert scorecard["explicit_abstention_required"] is True
    assert assessment["explicit_abstention"] is True
    assert 0 <= assessment["confidence"] <= 1
    assert "Source class alone cannot establish support" in text
