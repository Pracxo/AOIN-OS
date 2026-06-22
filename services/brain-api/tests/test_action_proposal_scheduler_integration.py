"""Scheduler action proposal integration tests."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.scheduler import (
    RecurrenceRule,
    ScheduleCreateRequest,
    SchedulerTickRequest,
)
from tests.scheduler_fakes import service_graph


class FakeActionProposalService:
    def __init__(self) -> None:
        self.requests: list[object] = []

    def create_proposal(self, request: object) -> object:
        self.requests.append(request)
        return request


def test_scheduler_tick_can_create_action_proposal_record() -> None:
    _, schedules, _, _, tick, *_ = service_graph()
    proposals = FakeActionProposalService()
    tick._action_proposal_service = proposals
    schedules.create_schedule(
        ScheduleCreateRequest(
            schedule_id="schedule-1",
            name="Propose",
            description="Create proposal only.",
            schedule_type="action_proposal",
            target_type="action_proposal",
            action_mode="propose_only",
            recurrence=RecurrenceRule(frequency="once"),
            start_at=datetime(2026, 1, 1, 9, tzinfo=UTC),
            owner_scope=["workspace:main"],
        )
    )

    run = tick.run_tick(
        SchedulerTickRequest(
            scope=["workspace:main"],
            mode="controlled",
            window_start=datetime(2026, 1, 1, 8, tzinfo=UTC),
            window_end=datetime(2026, 1, 1, 10, tzinfo=UTC),
            create_action_proposals=True,
        )
    )

    assert run.action_proposals_created == 1
    assert len(proposals.requests) == 1
