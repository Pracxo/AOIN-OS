from __future__ import annotations

from aion_brain.contracts.learning_synthesis import LearningSynthesisRequest
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.queues import QueueSummaryBuilder
from aion_brain.operator.repository import OperatorRepository
from aion_brain.operator.status_cards import StatusCardBuilder
from tests.learning_synthesis_helpers import AllowPolicy, bundle, create_experience_request


def test_operator_surfaces_learning_actions_queues_and_card() -> None:
    items = bundle()
    first = items.experiences.create_experience(create_experience_request("source-1"))
    second = items.experiences.create_experience(create_experience_request("source-2"))
    run = items.synthesizer.synthesize(
        LearningSynthesisRequest(
            mode="controlled",
            owner_scope=["workspace:main"],
            experience_ids=[first.experience_id, second.experience_id],
            create_skill_suggestions=True,
            create_regression_suggestions=True,
        )
    )
    high_pattern = run.patterns[0].model_copy(update={"severity": "high"})
    items.repository.save_pattern(high_pattern)

    action_center = ActionCenterService(
        OperatorRepository(),
        AllowPolicy(),
        learning_synthesis_repository=items.repository,
        skill_suggestion_service=items.skill_suggestions,
        regression_suggestion_service=items.regression_suggestions,
    )
    queues = QueueSummaryBuilder(
        learning_synthesis_repository=items.repository,
        skill_suggestion_service=items.skill_suggestions,
        regression_suggestion_service=items.regression_suggestions,
    ).build_queues(["workspace:main"])
    cards = StatusCardBuilder(learning_synthesizer=items.synthesizer).build_cards(
        ["workspace:main"]
    )

    actions = action_center.build_action_items(["workspace:main"])

    assert {action.source_type for action in actions} >= {
        "learning_pattern",
        "skill_suggestion",
        "regression_suggestion",
    }
    assert {"learning_patterns", "skill_suggestions", "regression_suggestions"} <= {
        queue.queue_type for queue in queues
    }
    assert any(card.card_id == "card-learning" for card in cards)
