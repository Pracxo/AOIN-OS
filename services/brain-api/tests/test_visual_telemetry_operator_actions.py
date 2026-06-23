from __future__ import annotations

from aion_brain.contracts.operator_actions import OperatorActionReviewRequest
from tests.operator_action_fakes import OperatorActionFixture, operator_action_request


def test_visual_telemetry_emits_operator_action_events() -> None:
    fixture = OperatorActionFixture()
    request = fixture.requests.create_request(operator_action_request(create_preview=True))
    fixture.previews.create_preview(request.operator_action_request_id, request.owner_scope)
    fixture.reviews.review(
        OperatorActionReviewRequest(
            operator_action_request_id=request.operator_action_request_id,
            decision="approve_preview_only",
            reason="reviewed",
        )
    )

    event_types = {getattr(event, "event_type", None) for event in fixture.telemetry.events}
    node_types = {getattr(event, "node_type", None) for event in fixture.telemetry.events}
    assert "operator_action_request_created" in event_types
    assert "operator_action_preview_created" in event_types
    assert "operator_action_review_recorded" in event_types
    assert "operator_action_request" in node_types
    assert "operator_action_preview" in node_types
    assert "operator_action_review" in node_types
