from __future__ import annotations

import pytest

from aion_brain.contracts.operator_actions import OperatorActionReviewRequest
from tests.operator_action_fakes import OperatorActionFixture, operator_action_request


def test_operator_action_request_service_enforces_authorization() -> None:
    fixture = OperatorActionFixture(enable_authorization=True)

    request = fixture.requests.create_request(
        operator_action_request(metadata={"roles": ["viewer"]})
    )

    assert request.status == "blocked"
    assert request.preview_id is None
    assert request.metadata["dry_run_authz_decision"]["role_allowed"] is False


def test_operator_action_preview_service_enforces_authorization() -> None:
    fixture = OperatorActionFixture(enable_authorization=True)
    request = fixture.requests.create_request(
        operator_action_request(metadata={"roles": ["viewer"]})
    )

    preview = fixture.previews.create_preview(
        request.operator_action_request_id,
        request.owner_scope,
    )

    assert preview.status == "blocked"
    assert any(item["blocker_type"] == "role_denied" for item in preview.blockers)


def test_operator_action_review_service_enforces_reviewer_role() -> None:
    fixture = OperatorActionFixture(enable_authorization=True)
    request = fixture.requests.create_request(
        operator_action_request(metadata={"roles": ["operator"]})
    )

    with pytest.raises(PermissionError):
        fixture.reviews.review(
            OperatorActionReviewRequest(
                operator_action_request_id=request.operator_action_request_id,
                decision="approve_preview_only",
                reason="reviewed",
                metadata={"roles": ["operator"]},
            )
        )

    review = fixture.reviews.review(
        OperatorActionReviewRequest(
            operator_action_request_id=request.operator_action_request_id,
            decision="approve_preview_only",
            reason="reviewed",
            metadata={"roles": ["reviewer"]},
        )
    )
    assert review.execution_allowed is False
