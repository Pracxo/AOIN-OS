from __future__ import annotations

from tests.belief_helpers import belief_bundle, create_claim


def test_contradiction_service_detects_direct_negation() -> None:
    bundle = belief_bundle()
    first = create_claim(bundle, "The feature flag is enabled.", source_id="source-1")
    create_claim(bundle, "Not the feature flag is enabled.", source_id="source-2")

    contradictions = bundle.contradictions.detect_for_claim(first.claim_id)

    assert len(contradictions) == 1
    assert contradictions[0].claim_id == first.claim_id
    assert contradictions[0].status == "open"


def test_contradiction_service_detects_metadata_fact_conflict() -> None:
    bundle = belief_bundle()
    first = create_claim(bundle, "The generic status is ready.", source_id="source-1")
    second = create_claim(bundle, "The generic status is blocked.", source_id="source-2")
    bundle.repository.save_claim(
        first.model_copy(update={"metadata": {"fact_key": "status", "fact_value": "ready"}})
    )
    bundle.repository.save_claim(
        second.model_copy(update={"metadata": {"fact_key": "status", "fact_value": "blocked"}})
    )

    contradictions = bundle.contradictions.detect_for_claim(first.claim_id)

    assert len(contradictions) == 1
    assert contradictions[0].contradicting_claim_id == second.claim_id


def test_contradiction_service_resolves_contradiction() -> None:
    bundle = belief_bundle()
    claim = create_claim(bundle)
    contradiction = bundle.contradictions.create_contradiction(
        claim_id=claim.claim_id,
        source_type="generic",
        source_id="source-2",
        reason="manual_conflict",
    )

    resolved = bundle.contradictions.resolve(
        contradiction.contradiction_id,
        "actor-1",
        "reviewed",
    )

    assert resolved.status == "resolved"
    assert resolved.resolved_at is not None
