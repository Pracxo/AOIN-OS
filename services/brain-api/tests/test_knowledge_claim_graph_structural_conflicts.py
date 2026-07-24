from __future__ import annotations

from test_knowledge_claim_graph_helpers import (
    MUCH_LATER,
    claim,
    scope,
    text_object,
    valid_interval,
)

from aion_brain.contracts.knowledge_claim_graph import ClaimPolarity, ClaimPredicateCardinality
from aion_brain.knowledge_intelligence.claim_graph import ControlledTemporalClaimEvidenceGraph


def test_structural_conflict_candidates_are_conservative_and_unresolved() -> None:
    service = ControlledTemporalClaimEvidenceGraph()
    left = claim("claim-0001", object_value=text_object("alpha"), polarity=ClaimPolarity.POSITIVE)
    right = claim("claim-0002", object_value=text_object("alpha"), polarity=ClaimPolarity.NEGATIVE)
    candidates = service.detect_structural_conflicts((left, right))
    assert len(candidates) == 1
    assert candidates[0].contradiction_resolved is False
    assert candidates[0].left_claim_true is False
    different_time = claim(
        "claim-0003",
        object_value=text_object("alpha"),
        polarity=ClaimPolarity.NEGATIVE,
        claim_scope=scope(intervals=(valid_interval("future", start=MUCH_LATER, end=None),)),
    )
    assert service.detect_structural_conflicts((left, different_time)) == ()


def test_many_valued_different_objects_are_not_conflicts_unless_exclusive() -> None:
    service = ControlledTemporalClaimEvidenceGraph()
    left = claim(
        "claim-0001",
        object_value=text_object("alpha"),
        predicate_cardinality=ClaimPredicateCardinality.MANY,
    )
    right = claim(
        "claim-0002",
        object_value=text_object("beta"),
        predicate_cardinality=ClaimPredicateCardinality.MANY,
    )
    assert service.detect_structural_conflicts((left, right)) == ()
    exclusive = claim(
        "claim-0003", object_value=text_object("beta"), objects_mutually_exclusive=True
    )
    exclusive_left = claim(
        "claim-0004", object_value=text_object("alpha"), objects_mutually_exclusive=True
    )
    assert service.detect_structural_conflicts((exclusive_left, exclusive))
