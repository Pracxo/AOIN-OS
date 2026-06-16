from __future__ import annotations

from aion_brain.contracts.decisions import DecisionFrameCreateRequest, DecisionOptionCreateRequest
from tests.decision_helpers import bundle


def test_decision_services_emit_visual_telemetry_events() -> None:
    services = bundle()
    frame = services.frame_service.create_frame(
        DecisionFrameCreateRequest(
            title="Choose",
            question="Which option?",
            owner_scope=["workspace:main"],
        )
    )
    services.option_service.create_option(
        DecisionOptionCreateRequest(
            decision_frame_id=frame.decision_frame_id,
            title="Option",
            description="Generic option.",
        )
    )

    event_types = {getattr(event, "event_type", "") for event in services.telemetry.events}
    assert "decision_frame_created" in event_types
    assert "decision_option_created" in event_types
