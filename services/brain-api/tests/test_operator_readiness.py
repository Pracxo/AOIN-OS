"""Operator readiness tests."""

from __future__ import annotations

from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.readiness import ReadinessAggregator
from aion_brain.operator.status_cards import StatusCardBuilder
from tests.operator_fakes import SCOPE, AllowPolicy, FakeListService, FakeRecord, repository


def test_readiness_release_ready_false_when_blocker_exists() -> None:
    actions = ActionCenterService(
        repository(),
        AllowPolicy(),
        None,
        resilience_service=FakeListService([FakeRecord("breaker-1", "open")]),
    )
    readiness = ReadinessAggregator(StatusCardBuilder(), actions).build_report(SCOPE)

    assert readiness.release_ready is False
    assert readiness.blockers


def test_readiness_local_ops_ready_true_when_core_checks_pass() -> None:
    actions = ActionCenterService(repository(), AllowPolicy())
    readiness = ReadinessAggregator(StatusCardBuilder(), actions).build_report(SCOPE)

    assert readiness.local_ops_ready is True
