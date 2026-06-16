from __future__ import annotations

from aion_brain.contracts.context import ContextPacket


def test_dialogue_decision_frames_remain_default_off() -> None:
    packet = ContextPacket(
        context_id="context-1",
        intent_id="intent-1",
        goal="clarify",
        known_context=[],
        retrieved_memory_ids=[],
        available_capability_ids=[],
        constraints=[],
        open_questions=["What outcome should be optimized?"],
        execution_limits={},
    )

    assert packet.execution_limits.get("create_decision_frame") is None
