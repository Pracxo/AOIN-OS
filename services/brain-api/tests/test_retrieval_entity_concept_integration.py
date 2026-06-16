from __future__ import annotations

from aion_brain.contracts.concepts import ConceptCreateRequest
from aion_brain.contracts.retrieval import RetrievalRequest
from aion_brain.retrieval.router import RetrievalRouter
from tests.entity_helpers import AllowPolicy, create_entity, entity_bundle


def test_retrieval_router_collects_entity_registry_items() -> None:
    bundle = entity_bundle()
    entity = create_entity(bundle, "Alpha Reference")
    router = RetrievalRouter(
        policy_adapter=AllowPolicy(),
        entity_query_service=bundle.entity_query_service,
    )

    result = router.retrieve(
        RetrievalRequest(
            retrieval_id="retrieval-entities",
            trace_id="trace-1",
            intent_id=None,
            query="alpha",
            scope=["workspace:main"],
            requested_sources=["entity_registry"],
            limit=10,
        )
    )

    assert result.items[0].source == "entity_registry"
    assert result.items[0].source_id == entity.entity_id


def test_retrieval_router_collects_concept_registry_items() -> None:
    bundle = entity_bundle()
    concept = bundle.concept_service.create(
        ConceptCreateRequest(
            name="Alpha Concept",
            description="A generic concept.",
            owner_scope=["workspace:main"],
        )
    )
    router = RetrievalRouter(
        policy_adapter=AllowPolicy(),
        concept_service=bundle.concept_service,
    )

    result = router.retrieve(
        RetrievalRequest(
            retrieval_id="retrieval-concepts",
            trace_id="trace-1",
            intent_id=None,
            query="alpha",
            scope=["workspace:main"],
            requested_sources=["concept_registry"],
            limit=10,
        )
    )

    assert result.items[0].source == "concept_registry"
    assert result.items[0].source_id == concept.concept_id
