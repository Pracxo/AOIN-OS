from __future__ import annotations

from aion_brain.contracts.operator_actions import OperatorActionReviewRequest
from aion_brain.operator.action_center import ActionCenterService
from tests.operator_action_fakes import OperatorActionFixture, operator_action_request


def test_operator_action_request_and_review_record_audit_and_provenance() -> None:
    fixture = OperatorActionFixture()
    request = fixture.requests.create_request(operator_action_request())
    review = fixture.reviews.review(
        OperatorActionReviewRequest(
            operator_action_request_id=request.operator_action_request_id,
            decision="approve_preview_only",
            reason="reviewed",
        )
    )

    assert fixture.audit.events
    assert any("operator_action_request_id" in str(event) for event in fixture.audit.events)
    assert review.operator_action_review_id
    assert fixture.provenance.links


def test_operator_action_center_surfaces_blockers() -> None:
    fixture = OperatorActionFixture()
    fixture.requests.create_request(operator_action_request())
    action_center = ActionCenterService(
        _ActionItemRepository(),
        policy_adapter=fixture.policy,
        operator_action_blocker_service=fixture.blockers,
    )

    items = action_center.build_action_items(["workspace:main"])

    assert any(item.recommended_action == "review_operator_action_preview" for item in items)


class _ActionItemRepository:
    def __init__(self) -> None:
        self.items: list[object] = []

    def save_action_item(self, item: object) -> object:
        self.items.append(item)
        return item

    def list_action_items(self, **_: object) -> list[object]:
        return []
