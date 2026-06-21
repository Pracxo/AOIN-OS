"""Decision journal to action proposal integration tests."""

from __future__ import annotations

from aion_brain.contracts.decisions import (
    DecisionFrameCreateRequest,
    DecisionOptionCreateRequest,
    DecisionRecordRequest,
)
from tests.decision_helpers import bundle


class ProposalSpy:
    """Collect proposal create requests."""

    def __init__(self) -> None:
        self.requests: list[object] = []

    def create_proposal(self, request: object) -> None:
        self.requests.append(request)


def test_decision_record_creates_proposal_only_when_option_metadata_requests_it() -> None:
    services = bundle()
    proposal_spy = ProposalSpy()
    services.journal.set_action_proposal_service(proposal_spy)
    frame = services.frame_service.create_frame(
        DecisionFrameCreateRequest(
            title="Choose next step",
            question="What should happen next?",
            owner_scope=["workspace:main"],
        )
    )
    default_option = services.option_service.create_option(
        DecisionOptionCreateRequest(
            decision_frame_id=frame.decision_frame_id,
            title="Observe",
            description="Observe only.",
            action_type="generic",
            target_type="noop",
        )
    )
    proposal_option = services.option_service.create_option(
        DecisionOptionCreateRequest(
            decision_frame_id=frame.decision_frame_id,
            title="Prepare action",
            description="Prepare an action proposal.",
            action_type="generic",
            target_type="noop",
            metadata={"create_action_proposal": True},
        )
    )

    services.journal.record_decision(
        DecisionRecordRequest(
            decision_frame_id=frame.decision_frame_id,
            selected_option_id=default_option.decision_option_id,
            rationale="Record only.",
        )
    )
    services.journal.record_decision(
        DecisionRecordRequest(
            decision_frame_id=frame.decision_frame_id,
            selected_option_id=proposal_option.decision_option_id,
            rationale="Create proposal.",
        )
    )

    assert len(proposal_spy.requests) == 1
