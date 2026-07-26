from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_candidate


def test_candidate_does_not_mutate_beliefs() -> None:
    assert sample_candidate().belief_mutated is False
