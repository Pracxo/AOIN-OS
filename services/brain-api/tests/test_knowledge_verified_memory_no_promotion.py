from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_candidate


def test_candidate_never_promotes_knowledge_automatically() -> None:
    candidate = sample_candidate()
    assert candidate.automatic_promotion is False
    assert candidate.verified_knowledge_created is False
