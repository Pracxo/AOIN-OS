"""Due item service for the local scheduler."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

from aion_brain.contracts.scheduler import ScheduleDueItem, ScheduleRecord
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.scheduler.policy_context import scheduler_policy_context


class DueItemService:
    """Materialize and query schedule due items."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_due_item(
        self,
        schedule: ScheduleRecord,
        due_at: datetime,
        tick_run_id: str | None,
        *,
        missed: bool = False,
        persist: bool = True,
    ) -> ScheduleDueItem:
        due_at = _utc(due_at)
        existing = _find_due_item(self._repository, schedule.schedule_id, due_at)
        if existing is not None:
            return existing
        due_item = ScheduleDueItem(
            due_item_id=(
                f"due-{uuid5(NAMESPACE_URL, f'{schedule.schedule_id}:{due_at.isoformat()}').hex}"
            ),
            schedule_id=schedule.schedule_id,
            trace_id=schedule.trace_id,
            actor_id=schedule.actor_id,
            workspace_id=schedule.workspace_id,
            due_at=due_at,
            status="missed" if missed else "due",
            target_type=schedule.target_type,
            action_mode=schedule.action_mode,
            target_payload=schedule.target_payload,
            owner_scope=schedule.owner_scope,
            created_from_tick_run_id=tick_run_id,
            result={"no_target_execution": True},
            metadata={"schedule_type": schedule.schedule_type},
            created_at=datetime.now(UTC),
        )
        if not persist:
            return due_item
        stored = _save_due_item(self._repository, due_item)
        emit_telemetry(
            self._telemetry_service,
            event_type="schedule_due_item_created",
            node_type="due_item",
            node_id=stored.due_item_id,
            intensity=0.75,
            trace_id=stored.trace_id,
            edge_from=stored.schedule_id,
            edge_to=stored.due_item_id,
            payload={"owner_scope": stored.owner_scope, "status": stored.status},
        )
        return stored

    def list_due_items(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        due_before: datetime | None = None,
        schedule_id: str | None = None,
        limit: int = 100,
    ) -> list[ScheduleDueItem]:
        authorize(
            self._policy_adapter,
            action_type="scheduler.due_item.read",
            resource_type="schedule_due_item",
            resource_id=schedule_id,
            scope=scope,
            risk_level="low",
            context=scheduler_policy_context("scheduler.due_item.read", scope),
        )
        list_due_items = getattr(self._repository, "list_due_items", None)
        if not callable(list_due_items):
            return []
        result = list_due_items(
            scope=scope,
            status=status,
            due_before=due_before,
            schedule_id=schedule_id,
            limit=limit,
        )
        return [item for item in result if isinstance(item, ScheduleDueItem)]


def _find_due_item(
    repository: object, schedule_id: str, due_at: datetime
) -> ScheduleDueItem | None:
    find = getattr(repository, "find_due_item", None)
    item = find(schedule_id, due_at) if callable(find) else None
    return item if isinstance(item, ScheduleDueItem) else None


def _save_due_item(repository: object, due_item: ScheduleDueItem) -> ScheduleDueItem:
    save = getattr(repository, "save_due_item", None)
    stored = save(due_item) if callable(save) else due_item
    return stored if isinstance(stored, ScheduleDueItem) else due_item


def _utc(value: datetime) -> datetime:
    return value.astimezone(UTC) if value.tzinfo is not None else value.replace(tzinfo=UTC)
