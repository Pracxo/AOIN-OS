from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from knowledge_verified_memory_test_helpers import sample_candidate


def test_parallel_candidate_evaluations_share_no_mutable_repository_state() -> None:
    with ThreadPoolExecutor(max_workers=4) as executor:
        fingerprints = tuple(
            executor.map(lambda _: sample_candidate().candidate_fingerprint, range(8))
        )
    assert len(set(fingerprints)) == 1
