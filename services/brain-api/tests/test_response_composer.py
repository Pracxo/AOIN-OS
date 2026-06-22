from __future__ import annotations

from aion_brain.contracts.responses import ResponseComposeRequest
from tests.dialogue_helpers import service_bundle


def test_response_composer_composes_from_reasoning_summary() -> None:
    bundle = service_bundle()

    response = bundle.response_composer.compose(
        ResponseComposeRequest(reasoning_result={"summary": "Prepared a generic plan."})
    )

    assert response.content == "Prepared a generic plan."
    assert response.status == "draft"


def test_response_composer_creates_clarification_response_when_required() -> None:
    bundle = service_bundle()

    response = bundle.response_composer.compose(
        ResponseComposeRequest(context={"open_questions": ["What is the goal?"]})
    )

    assert response.response_type == "clarification"
    assert "What is the goal?" in response.content


def test_response_composer_blocks_ungrounded_response_when_required() -> None:
    bundle = service_bundle()

    response = bundle.response_composer.compose(ResponseComposeRequest(require_grounding=True))

    assert response.status == "blocked"
    assert "grounding_required" in response.constraints
