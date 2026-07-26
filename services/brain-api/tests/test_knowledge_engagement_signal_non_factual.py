from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_signal


def test_engagement_signal_has_no_factual_or_knowledge_effect() -> None:
    signal = sample_signal()
    assert signal.factual_effect is False
    assert signal.knowledge_effect is False
    assert signal.cognitive_memory_effect is False
    assert signal.belief_effect is False
