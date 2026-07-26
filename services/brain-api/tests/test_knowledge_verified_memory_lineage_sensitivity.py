from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_candidate, sample_lineage


def test_changed_upstream_fingerprint_changes_lineage_fingerprint() -> None:
    first = sample_lineage()
    second = sample_lineage(suffix="002")
    assert first.lineage_fingerprint != second.lineage_fingerprint


def test_changed_claim_identity_changes_candidate_identity() -> None:
    first = sample_candidate()
    second = sample_candidate(claim_seed="claim-changed")
    assert first.candidate_identity_id != second.candidate_identity_id
