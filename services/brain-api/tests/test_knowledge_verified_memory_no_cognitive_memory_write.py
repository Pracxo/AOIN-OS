from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_candidate


def test_candidate_does_not_write_cognitive_memory() -> None:
    assert sample_candidate().cognitive_memory_written is False
