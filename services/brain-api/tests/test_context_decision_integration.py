from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.context.compiler import _packet
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.intent import IntentFrame


def test_context_compiler_includes_decision_metadata() -> None:
    packet = _packet(
        AIONEvent(
            event_id="event-1",
            source="test",
            event_type="question.answer",
            payload_type="test",
            payload={},
            timestamp=datetime.now(UTC),
            security_scope=["workspace:main"],
        ),
        IntentFrame(
            intent_id="intent-1",
            event_id="event-1",
            intent_type="question.answer",
            goal="choose",
            urgency="normal",
            confidence=0.8,
            risk_level="low",
            requires_memory=False,
            requires_capability=False,
            requires_approval=False,
        ),
        [
            {
                "source": "decision_journal",
                "source_id": "record-1",
                "metadata": {"decision_frame_id": "frame-1"},
            }
        ],
        [],
        [],
        [],
        [],
        [],
    )

    assert packet.execution_limits["decision_frame_id"] == "frame-1"
    assert packet.execution_limits["decision_record_id"] == "record-1"
