from __future__ import annotations

from aion_brain.contracts.operator_actions import OperatorActionReviewRequest
from tests.operator_action_fakes import OperatorActionFixture, operator_action_request


def test_review_service_approval_does_not_execute() -> None:
    fixture = OperatorActionFixture()
    request = fixture.requests.create_request(operator_action_request())

    review = fixture.reviews.review(
        OperatorActionReviewRequest(
            operator_action_request_id=request.operator_action_request_id,
            decision="approve_preview_only",
            reason="reviewed",
            approval_present=True,
        )
    )

    assert review.execution_allowed is False
    assert review.approval_present is True
    assert review.metadata["approval_does_not_execute"] is True
