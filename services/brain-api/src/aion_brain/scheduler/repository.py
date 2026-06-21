"""Persistence layer for the local AION scheduler."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    delete,
    insert,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.reminders import ReminderRecord, ReminderStatus, ReminderType
from aion_brain.contracts.scheduler import (
    DueItemStatus,
    RecurrenceRule,
    ScheduleActionMode,
    ScheduleDueItem,
    SchedulePolicy,
    SchedulePolicyAction,
    SchedulePolicyStatus,
    SchedulePolicyType,
    ScheduleRecord,
    SchedulerReport,
    SchedulerReportStatus,
    SchedulerTickMode,
    SchedulerTickRun,
    SchedulerTickStatus,
    ScheduleStatus,
    ScheduleTargetType,
    ScheduleType,
)
from aion_brain.schedules.repository import aion_schedules, schedule_metadata

scheduler_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_schedule_due_items = Table(
    "aion_schedule_due_items",
    scheduler_metadata,
    Column("due_item_id", Text, primary_key=True),
    Column("schedule_id", Text, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("due_at", DateTime(timezone=True), nullable=False),
    Column("status", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("action_mode", Text, nullable=False),
    Column("target_payload", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("created_from_tick_run_id", Text, nullable=True),
    Column("processed_at", DateTime(timezone=True), nullable=True),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_schedule_due_items_schedule_id", "schedule_id"),
    Index("ix_aion_schedule_due_items_trace_id", "trace_id"),
    Index("ix_aion_schedule_due_items_workspace_id", "workspace_id"),
    Index("ix_aion_schedule_due_items_due_at", "due_at"),
    Index("ix_aion_schedule_due_items_status", "status"),
    Index("ix_aion_schedule_due_items_created_at", "created_at"),
)

aion_reminders = Table(
    "aion_reminders",
    scheduler_metadata,
    Column("reminder_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("schedule_id", Text, nullable=True),
    Column("due_item_id", Text, nullable=True),
    Column("reminder_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("message", Text, nullable=False),
    Column("due_at", DateTime(timezone=True), nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("refs", json_payload_type, nullable=False),
    Column("snooze_count", Integer, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("acknowledged_at", DateTime(timezone=True), nullable=True),
    Column("snoozed_until", DateTime(timezone=True), nullable=True),
    Column("dismissed_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_reminders_trace_id", "trace_id"),
    Index("ix_aion_reminders_actor_id", "actor_id"),
    Index("ix_aion_reminders_workspace_id", "workspace_id"),
    Index("ix_aion_reminders_schedule_id", "schedule_id"),
    Index("ix_aion_reminders_due_item_id", "due_item_id"),
    Index("ix_aion_reminders_reminder_type", "reminder_type"),
    Index("ix_aion_reminders_due_at", "due_at"),
    Index("ix_aion_reminders_status", "status"),
    Index("ix_aion_reminders_created_at", "created_at"),
    Index("ix_aion_reminders_deleted_at", "deleted_at"),
)

aion_scheduler_tick_runs = Table(
    "aion_scheduler_tick_runs",
    scheduler_metadata,
    Column("tick_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("mode", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("tick_at", DateTime(timezone=True), nullable=False),
    Column("window_start", DateTime(timezone=True), nullable=False),
    Column("window_end", DateTime(timezone=True), nullable=False),
    Column("schedules_checked", Integer, nullable=False),
    Column("due_items_created", Integer, nullable=False),
    Column("reminders_created", Integer, nullable=False),
    Column("notifications_created", Integer, nullable=False),
    Column("action_proposals_created", Integer, nullable=False),
    Column("operator_items_created", Integer, nullable=False),
    Column("schedules_missed", Integer, nullable=False),
    Column("policy_decision_ids", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("errors", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_scheduler_tick_runs_trace_id", "trace_id"),
    Index("ix_aion_scheduler_tick_runs_workspace_id", "workspace_id"),
    Index("ix_aion_scheduler_tick_runs_mode", "mode"),
    Index("ix_aion_scheduler_tick_runs_status", "status"),
    Index("ix_aion_scheduler_tick_runs_tick_at", "tick_at"),
    Index("ix_aion_scheduler_tick_runs_created_at", "created_at"),
)

aion_schedule_policies = Table(
    "aion_schedule_policies",
    scheduler_metadata,
    Column("policy_id", Text, primary_key=True),
    Column("policy_type", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("conditions", json_payload_type, nullable=False),
    Column("action_on_violation", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_schedule_policies_policy_type", "policy_type"),
    Index("ix_aion_schedule_policies_status", "status"),
    Index("ix_aion_schedule_policies_action_on_violation", "action_on_violation"),
    Index("ix_aion_schedule_policies_created_at", "created_at"),
)

aion_scheduler_reports = Table(
    "aion_scheduler_reports",
    scheduler_metadata,
    Column("report_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text, nullable=False),
    Column("active_schedule_count", Integer, nullable=False),
    Column("due_item_count", Integer, nullable=False),
    Column("reminder_count", Integer, nullable=False),
    Column("missed_schedule_count", Integer, nullable=False),
    Column("failed_tick_count", Integer, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("recommendations", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_scheduler_reports_trace_id", "trace_id"),
    Index("ix_aion_scheduler_reports_workspace_id", "workspace_id"),
    Index("ix_aion_scheduler_reports_status", "status"),
    Index("ix_aion_scheduler_reports_created_at", "created_at"),
)


class SchedulerRepository:
    """Repository for schedules, due items, reminders, tick runs, and reports."""

    def __init__(
        self,
        database_url: str | None = None,
        *,
        engine: Engine | None = None,
        auto_create: bool = True,
    ) -> None:
        if engine is None:
            if database_url is None:
                raise ValueError("database_url or engine is required")
            if database_url.startswith("sqlite"):
                self._engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
            else:
                self._engine = create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_schedule(self, schedule: ScheduleRecord) -> ScheduleRecord:
        now = datetime.now(UTC)
        stored = schedule.model_copy(
            update={"created_at": schedule.created_at or now, "updated_at": now}
        )
        values = _schedule_values(stored)
        self._replace(aion_schedules, "schedule_id", stored.schedule_id, values)
        return stored

    def get_schedule(self, schedule_id: str) -> ScheduleRecord | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_schedules).where(aion_schedules.c.schedule_id == schedule_id)
                )
                .mappings()
                .first()
            )
        return _row_to_schedule(row) if row is not None else None

    def list_schedules(
        self,
        *,
        scope: list[str] | None = None,
        status: str | None = None,
        schedule_type: str | None = None,
        due_before: datetime | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[ScheduleRecord]:
        self._ensure_schema()
        statement = select(aion_schedules).order_by(aion_schedules.c.created_at.desc()).limit(limit)
        if status is not None:
            statement = statement.where(aion_schedules.c.status == status)
        if schedule_type is not None:
            statement = statement.where(aion_schedules.c.schedule_type == schedule_type)
        if due_before is not None:
            statement = statement.where(aion_schedules.c.next_due_at <= due_before)
        if not include_deleted:
            statement = statement.where(aion_schedules.c.deleted_at.is_(None))
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        schedules = [_row_to_schedule(row) for row in rows]
        return [item for item in schedules if _scope_matches(item.owner_scope, scope)][:limit]

    def save_due_item(self, due_item: ScheduleDueItem) -> ScheduleDueItem:
        stored = due_item.model_copy(
            update={"created_at": due_item.created_at or datetime.now(UTC)}
        )
        self._replace(
            aion_schedule_due_items,
            "due_item_id",
            stored.due_item_id,
            stored.model_dump(mode="python"),
        )
        return stored

    def find_due_item(self, schedule_id: str, due_at: datetime) -> ScheduleDueItem | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_schedule_due_items)
                    .where(aion_schedule_due_items.c.schedule_id == schedule_id)
                    .where(aion_schedule_due_items.c.due_at == due_at)
                )
                .mappings()
                .first()
            )
        return _row_to_due_item(row) if row is not None else None

    def list_due_items(
        self,
        *,
        scope: list[str] | None = None,
        status: str | None = None,
        due_before: datetime | None = None,
        schedule_id: str | None = None,
        limit: int = 100,
    ) -> list[ScheduleDueItem]:
        self._ensure_schema()
        statement = (
            select(aion_schedule_due_items)
            .order_by(aion_schedule_due_items.c.due_at.asc())
            .limit(limit)
        )
        if status is not None:
            statement = statement.where(aion_schedule_due_items.c.status == status)
        if due_before is not None:
            statement = statement.where(aion_schedule_due_items.c.due_at <= due_before)
        if schedule_id is not None:
            statement = statement.where(aion_schedule_due_items.c.schedule_id == schedule_id)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        due_items = [_row_to_due_item(row) for row in rows]
        return [item for item in due_items if _scope_matches(item.owner_scope, scope)][:limit]

    def save_reminder(self, reminder: ReminderRecord) -> ReminderRecord:
        stored = reminder.model_copy(
            update={"created_at": reminder.created_at or datetime.now(UTC)}
        )
        self._replace(
            aion_reminders,
            "reminder_id",
            stored.reminder_id,
            stored.model_dump(mode="python"),
        )
        return stored

    def get_reminder(self, reminder_id: str) -> ReminderRecord | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_reminders).where(aion_reminders.c.reminder_id == reminder_id)
                )
                .mappings()
                .first()
            )
        return _row_to_reminder(row) if row is not None else None

    def list_reminders(
        self,
        *,
        scope: list[str] | None = None,
        status: str | None = None,
        due_before: datetime | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[ReminderRecord]:
        self._ensure_schema()
        statement = select(aion_reminders).order_by(aion_reminders.c.due_at.asc()).limit(limit)
        if status is not None:
            statement = statement.where(aion_reminders.c.status == status)
        if due_before is not None:
            statement = statement.where(aion_reminders.c.due_at <= due_before)
        if not include_deleted:
            statement = statement.where(aion_reminders.c.deleted_at.is_(None))
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        reminders = [_row_to_reminder(row) for row in rows]
        return [item for item in reminders if _scope_matches(item.owner_scope, scope)][:limit]

    def save_tick_run(self, tick_run: SchedulerTickRun) -> SchedulerTickRun:
        now = datetime.now(UTC)
        stored = tick_run.model_copy(
            update={"created_at": tick_run.created_at or now, "completed_at": tick_run.completed_at}
        )
        values = stored.model_dump(mode="python", exclude={"due_items", "reminders"})
        values["result"] = {
            **stored.result,
            "due_item_ids": [item.due_item_id for item in stored.due_items],
            "reminder_ids": [item.reminder_id for item in stored.reminders],
        }
        self._replace(aion_scheduler_tick_runs, "tick_run_id", stored.tick_run_id, values)
        return stored

    def get_tick_run(self, tick_run_id: str) -> SchedulerTickRun | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_scheduler_tick_runs).where(
                        aion_scheduler_tick_runs.c.tick_run_id == tick_run_id
                    )
                )
                .mappings()
                .first()
            )
        return _row_to_tick_run(row) if row is not None else None

    def list_tick_runs(
        self,
        *,
        scope: list[str] | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[SchedulerTickRun]:
        self._ensure_schema()
        statement = (
            select(aion_scheduler_tick_runs)
            .order_by(aion_scheduler_tick_runs.c.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            statement = statement.where(aion_scheduler_tick_runs.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        runs = [_row_to_tick_run(row) for row in rows]
        return [item for item in runs if _scope_matches(item.owner_scope, scope)][:limit]

    def save_policy(self, policy: SchedulePolicy) -> SchedulePolicy:
        now = datetime.now(UTC)
        stored = policy.model_copy(
            update={"created_at": policy.created_at or now, "updated_at": policy.updated_at or now}
        )
        self._replace(
            aion_schedule_policies, "policy_id", stored.policy_id, stored.model_dump(mode="python")
        )
        return stored

    def list_policies(
        self,
        *,
        scope: list[str] | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[SchedulePolicy]:
        self._ensure_schema()
        statement = (
            select(aion_schedule_policies)
            .order_by(aion_schedule_policies.c.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            statement = statement.where(aion_schedule_policies.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        policies = [_row_to_policy(row) for row in rows]
        return [item for item in policies if _scope_matches(item.owner_scope, scope)][:limit]

    def save_report(self, report: SchedulerReport) -> SchedulerReport:
        stored = report.model_copy(update={"created_at": report.created_at or datetime.now(UTC)})
        self._replace(
            aion_scheduler_reports,
            "report_id",
            stored.report_id,
            stored.model_dump(mode="python"),
        )
        return stored

    def list_reports(
        self,
        *,
        scope: list[str] | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[SchedulerReport]:
        self._ensure_schema()
        statement = (
            select(aion_scheduler_reports)
            .order_by(aion_scheduler_reports.c.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            statement = statement.where(aion_scheduler_reports.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        reports = [_row_to_report(row) for row in rows]
        return [item for item in reports if _scope_matches(item.owner_scope, scope)][:limit]

    def _replace(self, table: Table, key: str, value: str, values: dict[str, Any]) -> None:
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(delete(table).where(table.c[key] == value))
            connection.execute(insert(table).values(**values))

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        schedule_metadata.create_all(self._engine)
        self._ensure_schedule_columns()
        scheduler_metadata.create_all(self._engine)
        self._schema_ready = True

    @staticmethod
    def _add_schedule_column_sql(column: str, column_type: str) -> str:
        return f"ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS {column} {column_type}"

    def _ensure_schedule_columns(self) -> None:
        columns = {
            "trace_id": "TEXT",
            "actor_id": "TEXT",
            "workspace_id": "TEXT",
            "name": "TEXT",
            "description": "TEXT",
            "target_type": "TEXT",
            "action_mode": "TEXT",
            "target_payload": "JSONB" if self._engine.dialect.name == "postgresql" else "JSON",
            "recurrence": "JSONB" if self._engine.dialect.name == "postgresql" else "JSON",
            "start_at": "TIMESTAMPTZ" if self._engine.dialect.name == "postgresql" else "TIMESTAMP",
            "end_at": "TIMESTAMPTZ" if self._engine.dialect.name == "postgresql" else "TIMESTAMP",
            "next_due_at": "TIMESTAMPTZ"
            if self._engine.dialect.name == "postgresql"
            else "TIMESTAMP",
            "last_due_at": "TIMESTAMPTZ"
            if self._engine.dialect.name == "postgresql"
            else "TIMESTAMP",
            "last_tick_run_id": "TEXT",
            "owner_scope": "JSONB" if self._engine.dialect.name == "postgresql" else "JSON",
            "created_by": "TEXT",
            "paused_at": "TIMESTAMPTZ"
            if self._engine.dialect.name == "postgresql"
            else "TIMESTAMP",
            "disabled_at": "TIMESTAMPTZ"
            if self._engine.dialect.name == "postgresql"
            else "TIMESTAMP",
            "deleted_at": "TIMESTAMPTZ"
            if self._engine.dialect.name == "postgresql"
            else "TIMESTAMP",
        }
        with self._engine.begin() as connection:
            for column, column_type in columns.items():
                try:
                    if self._engine.dialect.name == "postgresql":
                        connection.execute(text(self._add_schedule_column_sql(column, column_type)))
                    else:
                        connection.execute(
                            text(f"ALTER TABLE aion_schedules ADD COLUMN {column} {column_type}")
                        )
                except SQLAlchemyError:
                    continue


def _schedule_values(schedule: ScheduleRecord) -> dict[str, Any]:
    values = schedule.model_dump(mode="python")
    values.update(
        {
            "owner_type": "workflow",
            "owner_id": schedule.schedule_id,
            "schedule_expression": schedule.recurrence.frequency,
            "next_run_at": schedule.next_due_at,
            "last_run_at": schedule.last_due_at,
        }
    )
    return values


def _row_to_schedule(row: RowMapping) -> ScheduleRecord:
    recurrence = _dict(row["recurrence"]) or {"frequency": "manual"}
    return ScheduleRecord(
        schedule_id=str(row["schedule_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        name=str(row["name"] or row["schedule_id"]),
        description=str(row["description"] or "Legacy schedule metadata."),
        schedule_type=cast(ScheduleType, str(row["schedule_type"])),
        target_type=cast(ScheduleTargetType, str(row["target_type"] or "generic")),
        action_mode=cast(ScheduleActionMode, str(row["action_mode"] or "notify_only")),
        recurrence=RecurrenceRule.model_validate(recurrence),
        start_at=_datetime(row["start_at"] or row["created_at"]),
        end_at=_optional_datetime(row["end_at"]),
        timezone=str(row["timezone"] or "UTC"),
        status=cast(ScheduleStatus, str(row["status"])),
        next_due_at=_optional_datetime(row["next_due_at"] or row["next_run_at"]),
        last_due_at=_optional_datetime(row["last_due_at"] or row["last_run_at"]),
        last_tick_run_id=_optional_str(row["last_tick_run_id"]),
        owner_scope=_list(row["owner_scope"]) or ["workspace:main"],
        target_payload=_dict(row["target_payload"]),
        metadata=_dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        paused_at=_optional_datetime(row["paused_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
        deleted_at=_optional_datetime(row["deleted_at"]),
    )


def _row_to_due_item(row: RowMapping) -> ScheduleDueItem:
    return ScheduleDueItem(
        due_item_id=str(row["due_item_id"]),
        schedule_id=str(row["schedule_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        due_at=_datetime(row["due_at"]),
        status=cast(DueItemStatus, str(row["status"])),
        target_type=cast(ScheduleTargetType, str(row["target_type"])),
        action_mode=cast(ScheduleActionMode, str(row["action_mode"])),
        target_payload=_dict(row["target_payload"]),
        owner_scope=_list(row["owner_scope"]),
        created_from_tick_run_id=_optional_str(row["created_from_tick_run_id"]),
        processed_at=_optional_datetime(row["processed_at"]),
        result=_dict(row["result"]),
        metadata=_dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
    )


def _row_to_reminder(row: RowMapping) -> ReminderRecord:
    return ReminderRecord(
        reminder_id=str(row["reminder_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        schedule_id=_optional_str(row["schedule_id"]),
        due_item_id=_optional_str(row["due_item_id"]),
        reminder_type=cast(ReminderType, str(row["reminder_type"])),
        title=str(row["title"]),
        message=str(row["message"]),
        due_at=_datetime(row["due_at"]),
        status=cast(ReminderStatus, str(row["status"])),
        owner_scope=_list(row["owner_scope"]),
        refs=_list(row["refs"]),
        snooze_count=int(row["snooze_count"]),
        metadata=_dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        acknowledged_at=_optional_datetime(row["acknowledged_at"]),
        snoozed_until=_optional_datetime(row["snoozed_until"]),
        dismissed_at=_optional_datetime(row["dismissed_at"]),
        deleted_at=_optional_datetime(row["deleted_at"]),
    )


def _row_to_tick_run(row: RowMapping) -> SchedulerTickRun:
    return SchedulerTickRun(
        tick_run_id=str(row["tick_run_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        owner_scope=_list(row["owner_scope"]),
        mode=cast(SchedulerTickMode, str(row["mode"])),
        status=cast(SchedulerTickStatus, str(row["status"])),
        tick_at=_datetime(row["tick_at"]),
        window_start=_datetime(row["window_start"]),
        window_end=_datetime(row["window_end"]),
        schedules_checked=int(row["schedules_checked"]),
        due_items_created=int(row["due_items_created"]),
        reminders_created=int(row["reminders_created"]),
        notifications_created=int(row["notifications_created"]),
        action_proposals_created=int(row["action_proposals_created"]),
        operator_items_created=int(row["operator_items_created"]),
        schedules_missed=int(row["schedules_missed"]),
        policy_decision_ids=_list(row["policy_decision_ids"]),
        result=_dict(row["result"]),
        errors=_list(row["errors"]),
        created_at=_optional_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _row_to_policy(row: RowMapping) -> SchedulePolicy:
    return SchedulePolicy(
        policy_id=str(row["policy_id"]),
        policy_type=cast(SchedulePolicyType, str(row["policy_type"])),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(SchedulePolicyStatus, str(row["status"])),
        owner_scope=_list(row["owner_scope"]),
        conditions=_dict(row["conditions"]),
        action_on_violation=cast(SchedulePolicyAction, str(row["action_on_violation"])),
        metadata=_dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _row_to_report(row: RowMapping) -> SchedulerReport:
    return SchedulerReport(
        report_id=str(row["report_id"]),
        trace_id=_optional_str(row["trace_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        owner_scope=_list(row["owner_scope"]),
        status=cast(SchedulerReportStatus, str(row["status"])),
        title=str(row["title"]),
        summary=str(row["summary"]),
        active_schedule_count=int(row["active_schedule_count"]),
        due_item_count=int(row["due_item_count"]),
        reminder_count=int(row["reminder_count"]),
        missed_schedule_count=int(row["missed_schedule_count"]),
        failed_tick_count=int(row["failed_tick_count"]),
        findings=_list(row["findings"]),
        recommendations=_list(row["recommendations"]),
        metadata=_dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
    )


def _scope_matches(item_scope: list[str], requested_scope: list[str] | None) -> bool:
    return requested_scope is None or bool(set(item_scope) & set(requested_scope))


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _datetime(value: Any) -> datetime:
    parsed = _optional_datetime(value)
    if parsed is None:
        return datetime.now(UTC)
    return parsed


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")
