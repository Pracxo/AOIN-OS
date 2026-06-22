"""Operator control tower tests."""

from __future__ import annotations

from aion_brain.contracts.operator import OperatorOverviewRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.control_tower import OperatorControlTowerService
from aion_brain.operator.queues import QueueSummaryBuilder
from aion_brain.operator.readiness import ReadinessAggregator
from aion_brain.operator.runbooks import RunbookRegistry
from aion_brain.operator.status_cards import StatusCardBuilder
from tests.operator_fakes import SCOPE, AllowPolicy, FakeListService, FakeRecord, repository


def test_operator_control_tower_overview_aggregates_cards_queues_actions_readiness() -> None:
    repo = repository()
    actions = ActionCenterService(
        repo,
        AllowPolicy(),
        None,
        approval_service=FakeListService(
            [FakeRecord("approval-1", "pending", approval_scope=SCOPE)]
        ),
    )
    service = OperatorControlTowerService(
        status_cards=StatusCardBuilder(),
        queues=QueueSummaryBuilder(
            approval_service=FakeListService([FakeRecord("approval-1", "pending")])
        ),
        action_center=actions,
        readiness=ReadinessAggregator(StatusCardBuilder(), actions),
        runbooks=RunbookRegistry(),
        policy_adapter=AllowPolicy(),
    )

    overview = service.overview(OperatorOverviewRequest(owner_scope=SCOPE))

    assert overview.cards
    assert overview.queues
    assert overview.actions
    assert overview.readiness


def test_operator_control_tower_forwards_actor_context_to_policy() -> None:
    repo = repository()
    policy = AllowPolicy()
    actions = ActionCenterService(repo, policy)
    service = OperatorControlTowerService(
        status_cards=StatusCardBuilder(),
        queues=QueueSummaryBuilder(),
        action_center=actions,
        readiness=ReadinessAggregator(StatusCardBuilder(), actions),
        runbooks=RunbookRegistry(),
        policy_adapter=policy,
    )
    actor_context = ActorContext(
        actor_id="dev-user",
        actor_type="user",
        workspace_id="dev-workspace",
        roles=["owner"],
        permissions=["operator.overview.read", "operator.actions.read"],
        security_scope=SCOPE,
        dev_mode=True,
    )

    service.overview(
        OperatorOverviewRequest(owner_scope=SCOPE, include_runbooks=False),
        actor_context=actor_context,
    )

    assert policy.requests
    assert all(request.context["actor_context"]["dev_mode"] is True for request in policy.requests)
