from __future__ import annotations

from types import SimpleNamespace

from aion_brain.beliefs.claim_extractor import ClaimExtractor
from aion_brain.contracts.dialogue import DialogueTurnRequest
from tests.belief_helpers import belief_bundle
from tests.dialogue_helpers import service_bundle


def test_dialogue_turn_extracts_claims_only_when_requested() -> None:
    belief = belief_bundle()
    dialogue = service_bundle(
        claim_extractor=ClaimExtractor(),
        belief_service=belief.service,
        settings=SimpleNamespace(dialogue_enabled=True, belief_auto_extract_from_dialogue=False),
    )

    without_extraction = dialogue.turn_service.turn(
        DialogueTurnRequest(
            message="The dialogue layer can leave claims alone.",
            owner_scope=["workspace:main"],
            metadata={},
        )
    )
    with_extraction = dialogue.turn_service.turn(
        DialogueTurnRequest(
            message="The dialogue layer can extract generic claims.",
            owner_scope=["workspace:main"],
            metadata={"extract_claims": True},
        )
    )

    assert without_extraction.metadata["extracted_claim_ids"] == []
    assert len(with_extraction.metadata["extracted_claim_ids"]) == 1
    extracted_id = with_extraction.metadata["extracted_claim_ids"][0]
    assert belief.repository.get_claim(extracted_id) is not None


def test_dialogue_turn_auto_extracts_when_enabled() -> None:
    belief = belief_bundle()
    dialogue = service_bundle(
        claim_extractor=ClaimExtractor(),
        belief_service=belief.service,
        settings=SimpleNamespace(dialogue_enabled=True, belief_auto_extract_from_dialogue=True),
    )

    result = dialogue.turn_service.turn(
        DialogueTurnRequest(
            message="The dialogue auto extractor can create one claim.",
            owner_scope=["workspace:main"],
            metadata={},
        )
    )

    assert len(result.metadata["extracted_claim_ids"]) == 1
