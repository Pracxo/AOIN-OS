from __future__ import annotations

import pytest

from aion_brain.contracts.beliefs import BeliefSupportCreateRequest
from tests.belief_helpers import DenyPolicy, belief_bundle, create_claim


def test_support_service_creates_support_for_claim() -> None:
    bundle = belief_bundle()
    claim = create_claim(bundle)

    support = bundle.supports.create_support(
        BeliefSupportCreateRequest(
            claim_id=claim.claim_id,
            support_type="evidence",
            source_type="evidence",
            source_id="evidence-1",
            strength=0.8,
            confidence=0.8,
        )
    )

    assert support.claim_id == claim.claim_id
    assert bundle.supports.list_supports(claim.claim_id)[0].support_id == support.support_id


def test_contradicting_support_creates_contradiction() -> None:
    bundle = belief_bundle()
    claim = create_claim(bundle)

    bundle.supports.create_support(
        BeliefSupportCreateRequest(
            claim_id=claim.claim_id,
            support_type="evidence",
            source_type="evidence",
            source_id="evidence-conflict",
            relation_type="contradicts",
            strength=0.9,
            confidence=0.9,
        )
    )

    contradictions = bundle.repository.list_contradictions(claim_id=claim.claim_id)
    assert len(contradictions) == 1
    assert contradictions[0].contradiction_type == "evidence_contradiction"


def test_support_policy_deny_blocks_creation() -> None:
    bundle = belief_bundle(DenyPolicy())
    claim = create_claim(belief_bundle())
    bundle.repository.save_claim(claim)

    with pytest.raises(PermissionError):
        bundle.supports.create_support(
            BeliefSupportCreateRequest(
                claim_id=claim.claim_id,
                support_type="evidence",
                source_type="evidence",
                source_id="evidence-1",
            )
        )
