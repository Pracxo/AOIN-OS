"""Operator snapshot tests."""

from __future__ import annotations

from aion_brain.contracts.operator import OperatorSnapshotRequest
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.control_tower import OperatorControlTowerService
from aion_brain.operator.queues import QueueSummaryBuilder
from aion_brain.operator.readiness import ReadinessAggregator
from aion_brain.operator.runbooks import RunbookRegistry
from aion_brain.operator.snapshots import OperatorSnapshotService
from aion_brain.operator.status_cards import StatusCardBuilder
from tests.operator_fakes import SCOPE, AllowPolicy, repository


def test_operator_snapshot_service_creates_snapshot() -> None:
    repo = repository()
    actions = ActionCenterService(repo, AllowPolicy())
    readiness = ReadinessAggregator(StatusCardBuilder(), actions)
    control = OperatorControlTowerService(
        status_cards=StatusCardBuilder(),
        queues=QueueSummaryBuilder(),
        action_center=actions,
        readiness=readiness,
        runbooks=RunbookRegistry(),
        policy_adapter=AllowPolicy(),
    )
    service = OperatorSnapshotService(repo, control, AllowPolicy())

    snapshot = service.create_snapshot(OperatorSnapshotRequest(owner_scope=SCOPE))

    assert snapshot.status == "created"
    assert service.get_snapshot(snapshot.operator_snapshot_id, SCOPE) is not None
