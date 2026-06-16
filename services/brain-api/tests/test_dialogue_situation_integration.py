from __future__ import annotations

from aion_brain.contracts.situations import ContextContinuityRequest
from tests.situation_helpers import bundle


def test_dialogue_continuity_records_dialogue_turn_refs() -> None:
    services = bundle()
    record = services.continuity_service.record(
        ContextContinuityRequest(
            trace_id="trace-1",
            dialogue_session_id="dialogue-1",
            continuity_type="dialogue_turn",
            refs=["message-1"],
            owner_scope=["workspace:main"],
        )
    )

    assert record.continuity_type == "dialogue_turn"
    assert record.carried_refs == ["message-1"]
