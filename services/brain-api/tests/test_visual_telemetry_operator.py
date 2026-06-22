"""Operator visual telemetry tests."""

from aion_brain.operator.action_center import ActionCenterService
from tests.operator_fakes import (
    SCOPE,
    AllowPolicy,
    FakeListService,
    FakeRecord,
    FakeTelemetry,
    repository,
)


def test_visual_telemetry_emits_operator_action_item_event() -> None:
    telemetry = FakeTelemetry()
    service = ActionCenterService(
        repository(),
        AllowPolicy(),
        telemetry,
        approval_service=FakeListService(
            [FakeRecord("approval-1", "pending", approval_scope=SCOPE)]
        ),
    )

    service.build_action_items(SCOPE)

    assert telemetry.events
    event = telemetry.events[0]
    assert event.event_type == "operator_action_item_created"
    assert event.node_type == "action_item"


def test_operator_services_do_not_execute_actions() -> None:
    source = FakeListService([FakeRecord("approval-1", "pending", approval_scope=SCOPE)])
    service = ActionCenterService(
        repository(),
        AllowPolicy(),
        None,
        approval_service=source,
    )

    service.build_action_items(SCOPE)

    assert source.executed is False
