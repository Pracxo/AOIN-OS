"""Action review service tests."""

from __future__ import annotations

from aion_brain.contracts.action_proposals import ActionProposalReviewRequest
from tests.action_proposal_fakes import ActionFixture, DenyingGate, proposal_request


def test_action_review_service_creates_approval_request_for_high_risk_without_approval() -> None:
    fixture = ActionFixture()
    proposal = fixture.proposals.create_proposal(proposal_request(risk_level="high"))

    review = fixture.reviews.review(
        ActionProposalReviewRequest(
            action_proposal_id=proposal.action_proposal_id,
            decision="approve_for_handoff",
            reason="reviewed",
        )
    )

    assert review.decision == "request_approval"
    assert review.approval_request_id == "approval_required"
    assert review.blocker_refs


def test_action_review_service_blocks_autonomy_denied_proposal() -> None:
    fixture = ActionFixture()
    fixture.reviews._autonomy_governor = DenyingGate()
    proposal = fixture.proposals.create_proposal(proposal_request())

    review = fixture.reviews.review(
        ActionProposalReviewRequest(
            action_proposal_id=proposal.action_proposal_id,
            decision="approve_for_handoff",
            reason="reviewed",
        )
    )

    assert review.decision == "block"
    assert review.blocker_refs
