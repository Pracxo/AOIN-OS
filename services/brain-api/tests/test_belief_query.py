from __future__ import annotations

import pytest

from aion_brain.contracts.beliefs import BeliefQuery
from tests.belief_helpers import DenyPolicy, belief_bundle, create_claim


def test_belief_query_returns_matching_claims_and_supports() -> None:
    bundle = belief_bundle()
    create_claim(
        bundle,
        "The query layer can retrieve supported claims.",
        evidence_refs=["evidence-1"],
    )
    create_claim(bundle, "Another generic claim is stored.")

    result = bundle.query.query(BeliefQuery(query="supported", scope=["workspace:main"]))

    assert result.total_count == 1
    assert result.claims[0].claim_text.startswith("The query layer")
    assert result.supports


def test_belief_query_filters_scope() -> None:
    bundle = belief_bundle()
    claim = create_claim(bundle, "The scoped claim is private.")
    bundle.repository.save_claim(claim.model_copy(update={"owner_scope": ["workspace:other"]}))

    result = bundle.query.query(BeliefQuery(query="scoped", scope=["workspace:main"]))

    assert result.claims == []


def test_belief_query_policy_deny_fails_closed() -> None:
    bundle = belief_bundle(DenyPolicy())

    with pytest.raises(PermissionError):
        bundle.query.query(BeliefQuery(scope=["workspace:main"]))
