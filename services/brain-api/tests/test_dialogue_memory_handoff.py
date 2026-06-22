from __future__ import annotations

from aion_brain.contracts.dialogue import DialogueMessageCreateRequest
from tests.dialogue_helpers import FakeMemoryService, create_session, service_bundle


def test_dialogue_memory_handoff_runs_only_when_requested() -> None:
    memory = FakeMemoryService()
    bundle = service_bundle(memory_service=memory)
    session_id = create_session(bundle)
    message = bundle.message_service.create_message(
        DialogueMessageCreateRequest(dialogue_session_id=session_id, content="remember me")
    )

    result = bundle.handoff.remember_message_summary(message.message_id, ["workspace:main"])

    assert result["remembered"] is False
    assert memory.records == []


def test_dialogue_memory_handoff_calls_memory_governance_path() -> None:
    memory = FakeMemoryService()
    bundle = service_bundle(memory_service=memory)
    session_id = create_session(bundle)
    message = bundle.message_service.create_message(
        DialogueMessageCreateRequest(
            dialogue_session_id=session_id,
            content="remember me",
            metadata={"remember": True},
        )
    )

    result = bundle.handoff.remember_message_summary(message.message_id, ["workspace:main"])

    assert result["remembered"] is True
    assert len(memory.records) == 1
