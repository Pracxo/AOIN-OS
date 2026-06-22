from __future__ import annotations

from aion_brain.contracts.decisions import DecisionFrameCreateRequest
from tests.decision_helpers import bundle


def test_option_service_proposes_clarify_and_retrieve_context() -> None:
    services = bundle()
    frame = services.frame_service.create_frame(
        DecisionFrameCreateRequest(
            title="Choose next step",
            question="What should happen next?",
            owner_scope=["workspace:main"],
            constraints=["unclear_goal"],
        )
    )

    options = services.option_service.propose_default_options(frame.decision_frame_id)

    assert {option.option_type for option in options} >= {"clarify", "retrieve_more_context"}
