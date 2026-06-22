"""Scheduler operator integration tests."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.scheduler import ScheduleDueItem
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.queues import QueueSummaryBuilder
from aion_brain.operator.repository import OperatorRepository
from aion_brain.operator.status_cards import StatusCardBuilder


class FakeSchedulerQuery:
    def status(self, scope: list[str]) -> dict[str, object]:
        return {"status": "warning", "due_item_count": 1, "scope": scope}

    def list_due_items(self, scope: list[str], **kwargs: object) -> list[ScheduleDueItem]:
        return [
            ScheduleDueItem(
                due_item_id="due-1",
                schedule_id="schedule-1",
                due_at=datetime(2026, 1, 1, tzinfo=UTC),
                status="due",
                target_type="generic",
                action_mode="manual",
                owner_scope=scope,
            )
        ]

    def list_reminders(self, scope: list[str], **kwargs: object) -> list[object]:
        return []

    def list_tick_runs(self, scope: list[str], **kwargs: object) -> list[object]:
        return []

    def list_schedules(self, scope: list[str], **kwargs: object) -> list[object]:
        return []


def test_scheduler_surfaces_in_operator_status_queues_and_actions() -> None:
    scheduler = FakeSchedulerQuery()
    cards = StatusCardBuilder(scheduler_service=scheduler).build_cards(["workspace:main"])
    queues = QueueSummaryBuilder(scheduler_service=scheduler).build_queues(["workspace:main"])
    repo = OperatorRepository(
        engine=create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    )
    actions = ActionCenterService(
        repo,
        policy_adapter=None,
        scheduler_service=scheduler,
    )._scheduler_due_item_items(["workspace:main"])

    assert any(card.card_id == "card-scheduler" for card in cards)
    assert any(queue.title == "Due Items" for queue in queues)
    assert actions[0].source_type == "due_item"
