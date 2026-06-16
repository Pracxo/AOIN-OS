from __future__ import annotations

from types import SimpleNamespace

from aion_brain.contracts.dialogue import DialogueTurnRequest
from tests.dialogue_helpers import service_bundle
from tests.entity_helpers import create_entity, entity_bundle


def test_dialogue_turn_resolves_entities_only_when_requested() -> None:
    entities = entity_bundle()
    create_entity(entities)
    dialogue = service_bundle(
        entity_resolver=entities.resolver,
        settings=SimpleNamespace(dialogue_enabled=True, entity_auto_extract_from_dialogue=False),
    )

    without_extraction = dialogue.turn_service.turn(
        DialogueTurnRequest(
            message="Use [[Test Reference]].",
            owner_scope=["workspace:main"],
            metadata={},
        )
    )
    with_extraction = dialogue.turn_service.turn(
        DialogueTurnRequest(
            message="Use [[Test Reference]].",
            owner_scope=["workspace:main"],
            metadata={"extract_entities": True},
        )
    )

    assert without_extraction.metadata["entity_resolution_run_ids"] == []
    assert len(with_extraction.metadata["entity_resolution_run_ids"]) == 1
    assert entities.repository.list_mentions(scope=["workspace:main"], limit=10)


def test_dialogue_turn_auto_resolves_entities_when_enabled() -> None:
    entities = entity_bundle()
    create_entity(entities)
    dialogue = service_bundle(
        entity_resolver=entities.resolver,
        settings=SimpleNamespace(dialogue_enabled=True, entity_auto_extract_from_dialogue=True),
    )

    result = dialogue.turn_service.turn(
        DialogueTurnRequest(
            message="Use [[Test Reference]].",
            owner_scope=["workspace:main"],
            metadata={},
        )
    )

    assert len(result.metadata["entity_resolution_run_ids"]) == 1
