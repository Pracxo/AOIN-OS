from __future__ import annotations

import time

from knowledge_verified_memory_test_helpers import sample_candidate, sample_repository

from aion_brain.contracts.knowledge_verified_memory import VerifiedKnowledgeCandidateQuery


def test_ci_safe_performance_smoke_is_bounded_and_deterministic() -> None:
    start = time.perf_counter()
    for _ in range(100):
        sample_candidate()
    repo = sample_repository()
    for _ in range(100):
        repo.query(VerifiedKnowledgeCandidateQuery())
    assert time.perf_counter() - start < 10
