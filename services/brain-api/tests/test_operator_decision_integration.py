from __future__ import annotations

from aion_brain.contracts.decisions import DecisionFrameCreateRequest
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.queues import QueueSummaryBuilder
from aion_brain.operator.repository import OperatorRepository
from aion_brain.operator.status_cards import StatusCardBuilder
from tests.decision_helpers import bundle
from tests.kernel_fakes import AllowPolicy


def test_operator_surfaces_open_decision_frames() -> None:
    services = bundle()
    services.frame_service.create_frame(
        DecisionFrameCreateRequest(
            title="Choose",
            question="Which option?",
            owner_scope=["workspace:main"],
        )
    )

    items = ActionCenterService(
        OperatorRepository(),
        AllowPolicy(),
        decision_frame_service=services.frame_service,
    ).build_action_items(["workspace:main"])

    assert any(item.recommended_action == "review_open_decision_frame" for item in items)


def test_operator_status_and_queue_include_decisions() -> None:
    cards = StatusCardBuilder(decision_frame_service=object()).build_cards(["workspace:main"])
    queues = QueueSummaryBuilder(decision_frame_service=object()).build_queues(["workspace:main"])

    assert any(card.card_id == "card-decisions" for card in cards)
    assert any(queue.title == "Open Decision Frames" for queue in queues)
