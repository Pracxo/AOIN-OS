from __future__ import annotations

from knowledge_verified_memory_test_helpers import FIXED_TIME, sample_candidate, sample_repository


def test_fixed_inputs_produce_identical_candidates_and_snapshots() -> None:
    assert sample_candidate().candidate_fingerprint == sample_candidate().candidate_fingerprint
    first = sample_repository().snapshot("snapshot-001", created_at=FIXED_TIME)
    second = sample_repository().snapshot("snapshot-001", created_at=FIXED_TIME)
    assert first.snapshot_fingerprint == second.snapshot_fingerprint
