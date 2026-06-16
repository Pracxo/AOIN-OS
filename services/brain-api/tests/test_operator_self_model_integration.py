from __future__ import annotations

from aion_brain.contracts.self_model import LimitationCreateRequest
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.repository import OperatorRepository
from aion_brain.operator.status_cards import StatusCardBuilder
from tests.self_model_helpers import AllowPolicy, bundle


def test_operator_surfaces_self_model_cards_and_critical_limitations() -> None:
    services = bundle()
    limitation = services.limitations.create_limitation(
        LimitationCreateRequest(
            limitation_key="generic.critical_limit",
            category="generic",
            severity="critical",
            title="Critical limitation",
            description="A critical generic limitation.",
            owner_scope=["workspace:main"],
        )
    )
    cards = StatusCardBuilder(
        self_model_service=services.profile,
        capability_awareness_service=services.capabilities,
        limitation_service=services.limitations,
    ).build_cards(["workspace:main"])
    action_center = ActionCenterService(
        OperatorRepository(),
        AllowPolicy(),
        limitation_service=services.limitations,
    )

    actions = action_center.build_action_items(["workspace:main"])

    assert {"card-self_model", "card-capability_awareness", "card-limitations"} <= {
        card.card_id for card in cards
    }
    assert any(action.source_id == limitation.limitation_id for action in actions)
