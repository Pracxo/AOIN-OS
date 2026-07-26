from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_candidate


def test_candidate_identity_is_stable_for_same_claim_and_scope() -> None:
    first = sample_candidate()
    second = sample_candidate()
    assert first.candidate_identity_id == second.candidate_identity_id
    assert first.candidate_fingerprint == second.candidate_fingerprint


def test_candidate_identity_changes_when_scope_changes() -> None:
    first = sample_candidate()
    second = sample_candidate(scope_seed="scope-changed")
    assert first.candidate_identity_id != second.candidate_identity_id
