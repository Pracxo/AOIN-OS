from __future__ import annotations

from test_knowledge_claim_graph_helpers import graph_batch


def test_evidence_bundle_is_redacted_and_review_is_not_approval() -> None:
    service, registry, _claims, batch = graph_batch()
    repository, _decision = service.simulate_append(
        __import__(
            "aion_brain.knowledge_intelligence.claim_graph_repository",
            fromlist=["InMemoryTemporalClaimGraphRepository"],
        ).InMemoryTemporalClaimGraphRepository(),
        batch,
    )
    bundle = service.evidence_bundle(repository, source_registry_repository=registry)
    review = bundle.operator_review_items[0]
    assert review.operator_review_required is True
    assert review.approval_created is False
    assert review.implementation_authorization_created is False
    assert review.knowledge_promotion_authorized is False
    assert review.belief_mutation_authorized is False
    assert bundle.source_body_present is False
