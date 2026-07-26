from __future__ import annotations

from knowledge_verified_memory_test_helpers import FIXED_TIME, sample_repository


def test_repository_snapshot_is_deterministic_and_non_persistent() -> None:
    repo = sample_repository()
    first = repo.snapshot("snapshot-001", created_at=FIXED_TIME)
    second = repo.snapshot("snapshot-001", created_at=FIXED_TIME)
    assert first.snapshot_fingerprint == second.snapshot_fingerprint
    assert first.candidate_count == 1
    assert first.persistent_write_applied is False
