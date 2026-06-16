from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.dialogue import DialogueTurnRequest
from aion_brain.contracts.events import AIONEvent
from tests.kernel_fakes import kernel_container


def test_brain_think_includes_response_metadata_where_practical() -> None:
    container = kernel_container()
    trace = container.brain_loop_service.think(
        AIONEvent(
            event_id="event-1",
            source="test",
            event_type="question.answer",
            payload_type="json",
            payload={"goal": "Answer generically"},
            timestamp=datetime.now(UTC),
            security_scope=["workspace:main"],
        )
    )

    assert trace.outcome["response_id"]
    assert trace.outcome["response_status"] in {"draft", "blocked"}


def test_observability_failure_does_not_break_dialogue_turn() -> None:
    container = kernel_container()
    container.observability_service = object()

    result = container.dialogue_turn_service.turn(
        DialogueTurnRequest(message="hello", owner_scope=["workspace:main"])
    )

    assert result.response is not None
