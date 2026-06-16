from __future__ import annotations

from aion_brain.contracts.situations import SituationCreateRequest
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.queues import QueueSummaryBuilder
from aion_brain.operator.repository import OperatorRepository
from aion_brain.operator.status_cards import StatusCardBuilder
from tests.kernel_fakes import AllowPolicy
from tests.situation_helpers import bundle


def test_operator_status_cards_include_situations() -> None:
    services = bundle()
    services.situation_service.create(
        SituationCreateRequest(
            title="Current state",
            summary="Generic state.",
            owner_scope=["workspace:main"],
        )
    )

    cards = StatusCardBuilder(situation_service=services.situation_service).build_cards(
        ["workspace:main"]
    )

    assert any(card.card_id == "card-situations" for card in cards)


def test_operator_action_center_reports_stale_situations() -> None:
    services = bundle()
    situation = services.situation_service.create(
        SituationCreateRequest(
            title="Current state",
            summary="Generic state.",
            owner_scope=["workspace:main"],
        )
    )
    services.repository.save_situation(situation.model_copy(update={"status": "stale"}))

    items = ActionCenterService(
        OperatorRepository(),
        AllowPolicy(),
        situation_service=services.situation_service,
    ).build_action_items(["workspace:main"])

    assert any(item.recommended_action == "review_stale_situation" for item in items)


def test_operator_queue_builder_counts_failed_projection_runs() -> None:
    queues = QueueSummaryBuilder(situation_projector=object()).build_queues(["workspace:main"])

    assert any(queue.title == "Situation Projection Runs" for queue in queues)
