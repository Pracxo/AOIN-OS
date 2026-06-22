from __future__ import annotations

from aion_brain.contracts.entities import EntityResolutionRequest
from tests.entity_helpers import create_entity, entity_bundle


def test_resolver_matches_existing_entity_and_creates_link_when_not_dry_run() -> None:
    bundle = entity_bundle()
    entity = create_entity(bundle, "Test Reference")

    result = bundle.resolver.resolve(
        EntityResolutionRequest(
            owner_scope=["workspace:main"],
            source_type="dialogue_message",
            source_id="message-1",
            text="Please remember [[Test Reference]].",
            dry_run=False,
        )
    )

    assert result.status == "completed"
    assert result.mentions_resolved == 1
    assert result.created_mentions[0].entity_id == entity.entity_id
    assert result.created_links[0].target_id == entity.entity_id


def test_resolver_dry_run_persists_run_but_creates_no_entities_or_links() -> None:
    bundle = entity_bundle()

    result = bundle.resolver.resolve(
        EntityResolutionRequest(
            owner_scope=["workspace:main"],
            source_type="dialogue_message",
            source_id="message-1",
            text="Please remember [[Missing Reference]].",
            create_missing_entities=True,
            dry_run=True,
        )
    )

    assert result.status == "dry_run"
    assert result.created_entities == []
    assert result.created_links == []
    assert bundle.repository.get_resolution_result(result.resolution_run_id) is not None


def test_resolver_can_create_missing_entity_when_requested() -> None:
    bundle = entity_bundle()

    result = bundle.resolver.resolve(
        EntityResolutionRequest(
            owner_scope=["workspace:main"],
            source_type="dialogue_message",
            source_id="message-1",
            text="Please remember [[Missing Reference]].",
            create_missing_entities=True,
            dry_run=False,
        )
    )

    assert result.entities_created == 1
    assert result.created_entities[0].status == "proposed"
