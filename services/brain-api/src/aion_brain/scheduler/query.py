"""Read helpers for scheduler operator integrations."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.reminders import ReminderRecord
from aion_brain.contracts.scheduler import ScheduleDueItem, ScheduleRecord, SchedulerTickRun


class SchedulerQueryService:
    """Read-only scheduler query facade."""

    def __init__(self, repository: object) -> None:
        self._repository = repository

    def status(self, scope: list[str]) -> dict[str, object]:
        active = self.list_schedules(scope=scope, status="active", limit=1000)
        due = self.list_due_items(scope=scope, status="due", limit=1000)
        reminders = self.list_reminders(scope=scope, status="due", limit=1000)
        failed_ticks = self.list_tick_runs(scope=scope, status="failed", limit=1000)
        status = "failed" if failed_ticks else ("warning" if due or reminders else "healthy")
        return {
            "status": status,
            "active_schedule_count": len(active),
            "due_item_count": len(due),
            "due_reminder_count": len(reminders),
            "failed_tick_count": len(failed_ticks),
        }

    def list_schedules(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ScheduleRecord]:
        result = _call(self._repository, "list_schedules", scope=scope, status=status, limit=limit)
        return [item for item in result if isinstance(item, ScheduleRecord)]

    def list_due_items(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ScheduleDueItem]:
        result = _call(self._repository, "list_due_items", scope=scope, status=status, limit=limit)
        return [item for item in result if isinstance(item, ScheduleDueItem)]

    def list_reminders(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ReminderRecord]:
        result = _call(
            self._repository,
            "list_reminders",
            scope=scope,
            status=status,
            due_before=datetime.now(UTC),
            limit=limit,
        )
        return [item for item in result if isinstance(item, ReminderRecord)]

    def list_tick_runs(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[SchedulerTickRun]:
        result = _call(self._repository, "list_tick_runs", scope=scope, status=status, limit=limit)
        return [item for item in result if isinstance(item, SchedulerTickRun)]


def _call(repository: object, method_name: str, **kwargs: object) -> list[object]:
    method = getattr(repository, method_name, None)
    if not callable(method):
        return []
    result = method(**kwargs)
    return result if isinstance(result, list) else []
