from __future__ import annotations

from types import SimpleNamespace

from tests.entity_helpers import create_entity, entity_bundle
from tests.test_evidence_service import make_ingest_request, make_service


def test_evidence_ingest_resolves_entities_only_when_requested() -> None:
    entities = entity_bundle()
    create_entity(entities)
    service = make_service(
        entity_resolver=entities.resolver,
        settings=SimpleNamespace(entity_auto_extract_from_evidence=False),
    )

    service.ingest(make_ingest_request(content_text="Use [[Test Reference]]."))
    assert entities.repository.list_mentions(scope=["workspace:main"], limit=10) == []

    service.ingest(
        make_ingest_request(content_text="Use [[Test Reference]].").model_copy(
            update={
                "evidence_id": "evidence-2",
                "metadata": {"extract_entities": True},
            }
        )
    )

    mentions = entities.repository.list_mentions(scope=["workspace:main"], limit=10)
    assert len(mentions) == 1
    assert mentions[0].resolved is True


def test_evidence_ingest_auto_resolves_entities_when_enabled() -> None:
    entities = entity_bundle()
    create_entity(entities)
    service = make_service(
        entity_resolver=entities.resolver,
        settings=SimpleNamespace(entity_auto_extract_from_evidence=True),
    )

    service.ingest(make_ingest_request(content_text="Use [[Test Reference]]."))

    assert entities.repository.list_mentions(scope=["workspace:main"], limit=10)
