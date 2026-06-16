from __future__ import annotations

from aion_brain.contracts.retrieval import RetrievalRequest
from aion_brain.retrieval.router import RetrievalRouter
from tests.belief_helpers import belief_bundle, create_claim
from tests.test_retrieval_router import FakePolicyAdapter


def test_retrieval_router_collects_belief_state_items() -> None:
    bundle = belief_bundle()
    claim = create_claim(bundle, "Alpha belief state is available.", confidence=0.8)
    router = RetrievalRouter(
        policy_adapter=FakePolicyAdapter(),
        belief_query_service=bundle.query,
    )

    result = router.retrieve(
        RetrievalRequest(
            retrieval_id="retrieval-beliefs",
            trace_id="trace-1",
            intent_id=None,
            query="alpha",
            scope=["workspace:main"],
            requested_sources=["belief_state"],
            limit=10,
        )
    )

    assert result.items[0].source == "belief_state"
    assert result.items[0].source_id == claim.claim_id
    assert result.items[0].metadata["belief_state_is_not_absolute_truth"] is True


def test_retrieval_router_excludes_contradicted_beliefs_by_default() -> None:
    bundle = belief_bundle()
    claim = create_claim(bundle, "Alpha contradicted belief is present.", confidence=0.8)
    bundle.repository.save_claim(claim.model_copy(update={"status": "contradicted"}))
    router = RetrievalRouter(
        policy_adapter=FakePolicyAdapter(),
        belief_query_service=bundle.query,
    )

    result = router.retrieve(
        RetrievalRequest(
            retrieval_id="retrieval-beliefs",
            trace_id="trace-1",
            intent_id=None,
            query="alpha",
            scope=["workspace:main"],
            requested_sources=["belief_state"],
            limit=10,
        )
    )

    assert result.items == []


def test_retrieval_router_can_include_contradicted_beliefs_when_requested() -> None:
    bundle = belief_bundle()
    claim = create_claim(bundle, "Alpha contradicted belief is present.", confidence=0.8)
    bundle.repository.save_claim(claim.model_copy(update={"status": "contradicted"}))
    router = RetrievalRouter(
        policy_adapter=FakePolicyAdapter(),
        belief_query_service=bundle.query,
    )

    result = router.retrieve(
        RetrievalRequest(
            retrieval_id="retrieval-beliefs",
            trace_id="trace-1",
            intent_id=None,
            query="alpha",
            scope=["workspace:main"],
            requested_sources=["belief_state"],
            limit=10,
            metadata={"include_contradicted": True},
        )
    )

    assert result.items[0].source_id == claim.claim_id
    assert result.items[0].metadata["status"] == "contradicted"
