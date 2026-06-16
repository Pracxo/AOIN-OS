from __future__ import annotations

from aion_brain.contracts.dialogue import DialogueMessageCreateRequest
from tests.dialogue_helpers import create_session, service_bundle


def test_dialogue_message_service_creates_redacted_message() -> None:
    bundle = service_bundle()
    session_id = create_session(bundle)

    message = bundle.message_service.create_message(
        DialogueMessageCreateRequest(
            dialogue_session_id=session_id,
            content="token=sk-test-secret hello",
        )
    )

    assert message.content_redacted is True
    assert "sk-test-secret" not in message.content
    assert message.content_hash


def test_dialogue_message_service_soft_deletes_message() -> None:
    bundle = service_bundle()
    session_id = create_session(bundle)
    message = bundle.message_service.create_message(
        DialogueMessageCreateRequest(dialogue_session_id=session_id, content="hello")
    )

    deleted = bundle.message_service.soft_delete_message(message.message_id, "actor-1", "test")

    assert deleted is True
    assert bundle.message_service.get_message(message.message_id, ["workspace:main"]) is None
