"""Operator Action Center tests."""

from __future__ import annotations

from aion_brain.contracts.operator import OperatorAcknowledgementRequest
from aion_brain.operator.action_center import ActionCenterService
from tests.operator_fakes import (
    SCOPE,
    AllowPolicy,
    FakeAuditService,
    FakeListService,
    FakeRecord,
    FakeTelemetry,
    repository,
)


def test_action_center_creates_item_for_pending_approval() -> None:
    service = ActionCenterService(
        repository(),
        AllowPolicy(),
        FakeTelemetry(),
        approval_service=FakeListService(
            [FakeRecord("approval-1", "pending", priority="high", approval_scope=SCOPE)]
        ),
    )

    items = service.build_action_items(SCOPE)

    assert items[0].recommended_action == "review_pending_approval"


def test_action_center_creates_item_for_open_circuit_breaker() -> None:
    service = ActionCenterService(
        repository(),
        AllowPolicy(),
        FakeTelemetry(),
        resilience_service=FakeListService([FakeRecord("breaker-1", "open")]),
    )

    items = service.build_action_items(SCOPE)

    assert items[0].recommended_action == "inspect_degraded_component"


def test_action_center_creates_item_for_failed_audit_verification() -> None:
    service = ActionCenterService(
        repository(),
        AllowPolicy(),
        FakeTelemetry(),
        audit_service=FakeAuditService(FakeRecord("verify-1", "failed")),
    )

    items = service.build_action_items(SCOPE)

    assert items[0].recommended_action == "run_audit_verification"


def test_action_center_acknowledgement_does_not_resolve_source_issue() -> None:
    source = FakeListService([FakeRecord("approval-1", "pending", approval_scope=SCOPE)])
    repo = repository()
    service = ActionCenterService(repo, AllowPolicy(), FakeTelemetry(), approval_service=source)
    item = service.build_action_items(SCOPE)[0]

    ack = service.acknowledge(
        OperatorAcknowledgementRequest(
            action_item_id=item.action_item_id,
            source_type="approval",
            source_id="approval-1",
            reason="seen",
        )
    )

    assert ack.source_id == "approval-1"
    assert source.records[0].status == "pending"
    assert repo.get_action_item(item.action_item_id).status == "acknowledged"  # type: ignore[union-attr]
