from __future__ import annotations

from aion_brain.contracts.dialogue import DialogueTurnRequest
from tests.dialogue_helpers import FakeBrainLoop, service_bundle
from tests.self_model_helpers import bundle as self_model_bundle


def test_dialogue_turn_answers_what_is_aion_from_self_description() -> None:
    dialogue = service_bundle(brain_loop=FakeBrainLoop())
    self_model = self_model_bundle()
    dialogue.turn_service._self_description_service = self_model.description

    result = dialogue.turn_service.turn(
        DialogueTurnRequest(
            message="What is AION?",
            owner_scope=["workspace:main"],
            use_brain_loop=False,
        )
    )

    assert "Adaptive Intelligence Orchestration Nexus" in result.response.content
    assert result.response.metadata["self_description_source"] == "self_model"
