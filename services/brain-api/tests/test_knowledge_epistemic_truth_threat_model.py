from __future__ import annotations

from knowledge_claim_graph_evaluation_test_helpers import THREATS, read_text


def test_epistemic_threat_model_lists_required_threats_and_core_rule():
    text = read_text("docs/knowledge-intelligence/epistemic-threat-model.md")
    for threat in THREATS:
        assert threat in text
    assert "does not provide metaphysical certainty" in text
    assert "persistent assessment write" in text
    assert "knowledge-promotion bypass" in text
    assert "cognitive-belief mutation" in text
