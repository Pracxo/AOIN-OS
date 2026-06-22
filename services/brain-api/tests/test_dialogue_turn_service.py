from __future__ import annotations

from typing import Any

from aion_brain.contracts.dialogue import DialogueTurnRequest
from tests.dialogue_helpers import FakeBrainLoop, service_bundle


def test_dialogue_turn_service_creates_session_and_user_message() -> None:
    bundle = service_bundle(brain_loop=FakeBrainLoop())

    result = bundle.turn_service.turn(
        DialogueTurnRequest(message="Hello", owner_scope=["workspace:main"])
    )

    assert result.dialogue_session.status == "active"
    assert result.user_message.content == "Hello"
    assert result.response is not None


def test_dialogue_turn_service_calls_brain_loop_in_assist_mode() -> None:
    brain_loop = FakeBrainLoop()
    bundle = service_bundle(brain_loop=brain_loop)

    bundle.turn_service.turn(DialogueTurnRequest(message="Hello", owner_scope=["workspace:main"]))

    assert brain_loop.calls == 1


def test_dialogue_turn_service_never_triggers_controlled_execution() -> None:
    bundle = service_bundle(brain_loop=FakeBrainLoop())

    result = bundle.turn_service.turn(
        DialogueTurnRequest(message="Hello", owner_scope=["workspace:main"], mode="dry_run")
    )

    assert result.metadata["mode"] == "dry_run"


def test_dialogue_turn_service_creates_clarification_when_brain_loop_requires_it() -> None:
    bundle = service_bundle(brain_loop=FakeBrainLoop(requires_clarification=True))

    result = bundle.turn_service.turn(
        DialogueTurnRequest(message="Hello", owner_scope=["workspace:main"])
    )

    assert result.clarification is not None
    assert result.response is not None
    assert result.response.response_type == "clarification"


def test_dialogue_turn_result_includes_grounding_status_when_present(
    monkeypatch: Any,
) -> None:
    bundle = service_bundle(brain_loop=FakeBrainLoop())
    original_compose = bundle.response_composer.compose

    def compose_with_grounding(request: object) -> object:
        response = original_compose(request)
        return response.model_copy(
            update={
                "metadata": {
                    **response.metadata,
                    "citation_map_id": "citation-map-1",
                    "grounding_verification_id": "grounding-verification-1",
                    "grounding_status": "passed",
                }
            }
        )

    monkeypatch.setattr(bundle.response_composer, "compose", compose_with_grounding)

    result = bundle.turn_service.turn(
        DialogueTurnRequest(message="Hello", owner_scope=["workspace:main"])
    )

    assert result.metadata["citation_map_id"] == "citation-map-1"
    assert result.metadata["grounding_status"] == "passed"
