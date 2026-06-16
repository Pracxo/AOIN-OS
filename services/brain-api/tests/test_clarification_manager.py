from __future__ import annotations

from aion_brain.contracts.dialogue import ClarificationAnswerRequest, DialogueMessageCreateRequest
from tests.dialogue_helpers import create_session, service_bundle


def test_clarification_manager_creates_clarification() -> None:
    bundle = service_bundle()
    session_id = create_session(bundle)

    clarification = bundle.clarification_manager.create_clarification(
        session_id,
        None,
        "trace-1",
        "What should happen next?",
        "missing_goal",
        True,
        {},
    )

    assert clarification.status == "pending"
    assert bundle.clarification_manager.list_pending(["workspace:main"]) == [clarification]


def test_clarification_answer_creates_clarification_answer_message() -> None:
    bundle = service_bundle()
    session_id = create_session(bundle)
    message = bundle.message_service.create_message(
        DialogueMessageCreateRequest(dialogue_session_id=session_id, content="hello")
    )
    clarification = bundle.clarification_manager.create_clarification(
        session_id,
        message.message_id,
        "trace-1",
        "What next?",
        "missing_goal",
        True,
        {},
    )

    answered = bundle.clarification_manager.answer(
        ClarificationAnswerRequest(
            clarification_id=clarification.clarification_id,
            answer="Continue.",
        )
    )

    assert answered.status == "answered"
    assert answered.answer_message_id is not None
