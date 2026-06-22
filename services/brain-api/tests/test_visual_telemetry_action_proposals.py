"""Action proposal visual telemetry tests."""

from __future__ import annotations

from aion_brain.contracts.action_proposals import ActionProposalReviewRequest
from aion_brain.contracts.execution_handoffs import ExecutionHandoffRequest
from tests.action_proposal_fakes import ActionFixture, proposal_request


def test_visual_telemetry_emits_action_proposal_events() -> None:
    fixture = ActionFixture()
    proposal = fixture.proposals.create_proposal(proposal_request())
    fixture.reviews.review(
        ActionProposalReviewRequest(
            action_proposal_id=proposal.action_proposal_id,
            decision="approve_for_handoff",
            reason="reviewed",
            approval_present=True,
        )
    )
    fixture.handoffs.handoff(
        ExecutionHandoffRequest(
            action_proposal_id=proposal.action_proposal_id,
            handoff_type="dry_run",
            target_system="noop",
        )
    )

    assert {getattr(event, "event_type", None) for event in fixture.telemetry.events} >= {
        "action_proposal_created",
        "action_proposal_reviewed",
        "execution_handoff_created",
    }
