from __future__ import annotations

import pytest

from aion_brain.contracts.beliefs import BeliefClaimCreateRequest
from tests.belief_helpers import DenyPolicy, belief_bundle, create_claim


def test_belief_service_creates_claim_with_normalized_hash() -> None:
    bundle = belief_bundle()

    claim = create_claim(bundle, "The local belief ledger is active.", evidence_refs=["ev-1"])

    assert claim.claim_id.startswith("belief-claim-")
    assert claim.normalized_claim == "the local belief ledger is active"
    assert claim.claim_hash
    assert claim.status == "supported"
    assert bundle.repository.get_claim(claim.claim_id) == claim


def test_belief_service_deduplicates_same_source_claim() -> None:
    bundle = belief_bundle()

    first = create_claim(bundle, "The kernel is assembled.", source_id="source-a")
    second = create_claim(bundle, "The kernel is assembled.", source_id="source-a")

    assert second.claim_id == first.claim_id


def test_belief_service_revision_updates_status_and_confidence() -> None:
    bundle = belief_bundle()
    claim = create_claim(bundle, "A claim can be revised.")

    revision = bundle.service.revise_claim(
        claim.claim_id,
        "rejected",
        0.1,
        "superseded",
        "actor-1",
    )

    updated = bundle.repository.get_claim(claim.claim_id)
    assert revision.from_status == "uncertain"
    assert revision.to_status == "rejected"
    assert updated is not None
    assert updated.status == "rejected"
    assert updated.confidence == 0.1


def test_belief_service_soft_delete_archives_claim() -> None:
    bundle = belief_bundle()
    claim = create_claim(bundle, "A claim can be archived.")

    assert bundle.service.soft_delete_claim(claim.claim_id, "actor-1", "cleanup") is True

    updated = bundle.repository.get_claim(claim.claim_id)
    assert updated is not None
    assert updated.status == "archived"
    assert updated.deleted_at is not None


def test_policy_deny_blocks_claim_creation() -> None:
    bundle = belief_bundle(DenyPolicy())

    with pytest.raises(PermissionError):
        bundle.service.create_claim(
            BeliefClaimCreateRequest(
                claim_text="This claim should not persist.",
                source_type="generic",
                owner_scope=["workspace:main"],
            )
        )
