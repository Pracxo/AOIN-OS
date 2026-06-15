"""Persistence for cognitive cycle templates, runs, steps, and consolidation."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.cycles import (
    CognitiveCycleRun,
    CognitiveCycleRunRequest,
    CognitiveCycleStep,
    CognitiveCycleStepRun,
    CognitiveCycleTemplate,
    CycleMode,
    CycleRiskLevel,
    CycleRunStatus,
    CycleStepRunStatus,
    CycleStepType,
    CycleTemplateStatus,
    CycleType,
    SleepConsolidationRecord,
)

cycle_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_cognitive_cycle_templates = Table(
    "aion_cognitive_cycle_templates",
    cycle_metadata,
    Column("cycle_template_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("cycle_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("steps", json_payload_type, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("requires_approval", Boolean, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_cycle_templates_name", "name"),
    Index("ix_aion_cycle_templates_type", "cycle_type"),
    Index("ix_aion_cycle_templates_status", "status"),
    Index("ix_aion_cycle_templates_risk", "risk_level"),
    Index("ix_aion_cycle_templates_created", "created_at"),
)

aion_cognitive_cycle_runs = Table(
    "aion_cognitive_cycle_runs",
    cycle_metadata,
    Column("cycle_run_id", Text, primary_key=True),
    Column("cycle_template_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("cycle_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("input", json_payload_type, nullable=False),
    Column("output", json_payload_type, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("risk_assessment_id", Text, nullable=True),
    Column("approval_request_id", Text, nullable=True),
    Column("autonomy_decision_id", Text, nullable=True),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_cycle_runs_template", "cycle_template_id"),
    Index("ix_aion_cycle_runs_trace", "trace_id"),
    Index("ix_aion_cycle_runs_actor", "actor_id"),
    Index("ix_aion_cycle_runs_workspace", "workspace_id"),
    Index("ix_aion_cycle_runs_type", "cycle_type"),
    Index("ix_aion_cycle_runs_status", "status"),
    Index("ix_aion_cycle_runs_mode", "mode"),
    Index("ix_aion_cycle_runs_created", "created_at"),
)

aion_cognitive_cycle_steps = Table(
    "aion_cognitive_cycle_steps",
    cycle_metadata,
    Column("cycle_step_run_id", Text, primary_key=True),
    Column(
        "cycle_run_id",
        Text,
        ForeignKey("aion_cognitive_cycle_runs.cycle_run_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("step_id", Text, nullable=False),
    Column("step_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("input", json_payload_type, nullable=False),
    Column("output", json_payload_type, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_cycle_steps_run", "cycle_run_id"),
    Index("ix_aion_cycle_steps_step", "step_id"),
    Index("ix_aion_cycle_steps_type", "step_type"),
    Index("ix_aion_cycle_steps_status", "status"),
    Index("ix_aion_cycle_steps_created", "created_at"),
)

aion_sleep_consolidation_records = Table(
    "aion_sleep_consolidation_records",
    cycle_metadata,
    Column("consolidation_id", Text, primary_key=True),
    Column("cycle_run_id", Text, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("working_memory_slots_reviewed", Integer, nullable=False),
    Column("memories_decayed", Integer, nullable=False),
    Column("conflicts_detected", Integer, nullable=False),
    Column("compaction_runs", Integer, nullable=False),
    Column("reflections_created", Integer, nullable=False),
    Column("skill_candidates_created", Integer, nullable=False),
    Column("regression_cases_checked", Integer, nullable=False),
    Column("visual_snapshots_created", Integer, nullable=False),
    Column("summary", Text, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_sleep_records_run", "cycle_run_id"),
    Index("ix_aion_sleep_records_trace", "trace_id"),
    Index("ix_aion_sleep_records_actor", "actor_id"),
    Index("ix_aion_sleep_records_workspace", "workspace_id"),
    Index("ix_aion_sleep_records_created", "created_at"),
)


class CognitiveCycleRepository:
    """Repository for cognitive cycle records."""

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
            self._engine = _create_engine(database_url)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_template(self, template: CognitiveCycleTemplate) -> CognitiveCycleTemplate:
        """Upsert one cycle template."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = template.model_copy(
            update={
                "created_at": template.created_at or now,
                "updated_at": now,
            }
        )
        values = stored.model_dump(mode="python")
        values["steps"] = [step.model_dump(mode="json") for step in stored.steps]
        self._upsert(aion_cognitive_cycle_templates, "cycle_template_id", values)
        return stored

    def get_template(self, cycle_template_id: str) -> CognitiveCycleTemplate | None:
        """Return one cycle template."""
        row = self._get(aion_cognitive_cycle_templates, "cycle_template_id", cycle_template_id)
        return _template_from_row(row) if row is not None else None

    def list_templates(
        self,
        *,
        cycle_type: str | None = None,
        status: str | None = None,
    ) -> list[CognitiveCycleTemplate]:
        """List cycle templates."""
        self._ensure_schema()
        query = select(aion_cognitive_cycle_templates)
        if cycle_type is not None:
            query = query.where(aion_cognitive_cycle_templates.c.cycle_type == cycle_type)
        if status is not None:
            query = query.where(aion_cognitive_cycle_templates.c.status == status)
        query = query.order_by(aion_cognitive_cycle_templates.c.created_at.desc())
        with self._engine.connect() as connection:
            rows = connection.execute(query).mappings().all()
        return [_template_from_row(row) for row in rows]

    def save_run(self, run: CognitiveCycleRun) -> CognitiveCycleRun:
        """Upsert one cycle run."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = run.model_copy(
            update={
                "created_at": run.created_at or now,
                "updated_at": now,
            }
        )
        values = stored.model_dump(mode="python", exclude={"steps"})
        self._upsert(aion_cognitive_cycle_runs, "cycle_run_id", values)
        for step in stored.steps:
            self.save_step(step)
        return stored

    def get_run(self, cycle_run_id: str) -> CognitiveCycleRun | None:
        """Return one run with step records."""
        row = self._get(aion_cognitive_cycle_runs, "cycle_run_id", cycle_run_id)
        if row is None:
            return None
        run = _run_from_row(row)
        return run.model_copy(update={"steps": self.list_steps(cycle_run_id)})

    def list_runs(
        self,
        *,
        scope: list[str],
        cycle_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[CognitiveCycleRun]:
        """List runs visible to a scope."""
        self._ensure_schema()
        query = select(aion_cognitive_cycle_runs)
        if cycle_type is not None:
            query = query.where(aion_cognitive_cycle_runs.c.cycle_type == cycle_type)
        if status is not None:
            query = query.where(aion_cognitive_cycle_runs.c.status == status)
        query = query.order_by(aion_cognitive_cycle_runs.c.created_at.desc()).limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(query).mappings().all()
        return [
            run.model_copy(update={"steps": self.list_steps(run.cycle_run_id)})
            for run in (_run_from_row(row) for row in rows)
            if _scope_matches(run.owner_scope, scope)
        ]

    def save_step(self, step: CognitiveCycleStepRun) -> CognitiveCycleStepRun:
        """Upsert one cycle step run."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = step.model_copy(
            update={
                "created_at": step.created_at or now,
                "updated_at": now,
            }
        )
        self._upsert(
            aion_cognitive_cycle_steps,
            "cycle_step_run_id",
            stored.model_dump(mode="python"),
        )
        return stored

    def list_steps(self, cycle_run_id: str) -> list[CognitiveCycleStepRun]:
        """List step runs for a cycle run."""
        self._ensure_schema()
        query = (
            select(aion_cognitive_cycle_steps)
            .where(aion_cognitive_cycle_steps.c.cycle_run_id == cycle_run_id)
            .order_by(aion_cognitive_cycle_steps.c.created_at.asc())
        )
        with self._engine.connect() as connection:
            rows = connection.execute(query).mappings().all()
        return [_step_from_row(row) for row in rows]

    def save_sleep_record(
        self,
        record: SleepConsolidationRecord,
    ) -> SleepConsolidationRecord:
        """Upsert one sleep consolidation record."""
        self._ensure_schema()
        stored = record.model_copy(update={"created_at": record.created_at or datetime.now(UTC)})
        self._upsert(
            aion_sleep_consolidation_records,
            "consolidation_id",
            stored.model_dump(mode="python"),
        )
        return stored

    def get_sleep_record(self, cycle_run_id: str) -> SleepConsolidationRecord | None:
        """Return the newest sleep consolidation record for one run."""
        self._ensure_schema()
        query = (
            select(aion_sleep_consolidation_records)
            .where(aion_sleep_consolidation_records.c.cycle_run_id == cycle_run_id)
            .order_by(aion_sleep_consolidation_records.c.created_at.desc())
        )
        with self._engine.connect() as connection:
            row = connection.execute(query).mappings().first()
        return _sleep_from_row(row) if row is not None else None

    def _upsert(self, table: Table, key: str, values: dict[str, Any]) -> None:
        with self._engine.begin() as connection:
            existing = connection.execute(select(table.c[key]).where(table.c[key] == values[key]))
            if existing.first() is None:
                connection.execute(insert(table).values(**values))
            else:
                connection.execute(
                    update(table).where(table.c[key] == values[key]).values(**values)
                )

    def _get(self, table: Table, key: str, value: str) -> RowMapping | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            return connection.execute(select(table).where(table.c[key] == value)).mappings().first()

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        cycle_metadata.create_all(self._engine)
        self._schema_ready = True


def new_run_from_request(
    request: CognitiveCycleRunRequest,
    cycle_run_id: str,
    now: datetime,
) -> CognitiveCycleRun:
    """Create a pending run from a request."""
    return CognitiveCycleRun(
        cycle_run_id=cycle_run_id,
        cycle_template_id=request.cycle_template_id,
        trace_id=request.trace_id,
        actor_id=request.actor_id,
        workspace_id=request.workspace_id,
        cycle_type=request.cycle_type,
        status="pending",
        mode=request.mode,
        owner_scope=request.owner_scope,
        steps=[],
        input=request.input,
        output={},
        error={},
        risk_assessment_id=None,
        approval_request_id=None,
        autonomy_decision_id=None,
        started_at=None,
        completed_at=None,
        created_at=now,
        updated_at=now,
    )


def _template_from_row(row: RowMapping) -> CognitiveCycleTemplate:
    return CognitiveCycleTemplate(
        cycle_template_id=str(row["cycle_template_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        cycle_type=cast(CycleType, row["cycle_type"]),
        status=cast(CycleTemplateStatus, row["status"]),
        owner_scope=_list_str(row["owner_scope"]),
        steps=[CognitiveCycleStep(**item) for item in _list_dict(row["steps"])],
        risk_level=cast(CycleRiskLevel, row["risk_level"]),
        requires_approval=bool(row["requires_approval"]),
        metadata=_dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _run_from_row(row: RowMapping) -> CognitiveCycleRun:
    return CognitiveCycleRun(
        cycle_run_id=str(row["cycle_run_id"]),
        cycle_template_id=_optional_str(row["cycle_template_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        cycle_type=cast(CycleType, row["cycle_type"]),
        status=cast(CycleRunStatus, row["status"]),
        mode=cast(CycleMode, row["mode"]),
        owner_scope=_list_str(row["owner_scope"]),
        steps=[],
        input=_dict(row["input"]),
        output=_dict(row["output"]),
        error=_dict(row["error"]),
        risk_assessment_id=_optional_str(row["risk_assessment_id"]),
        approval_request_id=_optional_str(row["approval_request_id"]),
        autonomy_decision_id=_optional_str(row["autonomy_decision_id"]),
        started_at=_optional_datetime(row["started_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
    )


def _step_from_row(row: RowMapping) -> CognitiveCycleStepRun:
    return CognitiveCycleStepRun(
        cycle_step_run_id=str(row["cycle_step_run_id"]),
        cycle_run_id=str(row["cycle_run_id"]),
        step_id=str(row["step_id"]),
        step_type=cast(CycleStepType, row["step_type"]),
        status=cast(CycleStepRunStatus, row["status"]),
        input=_dict(row["input"]),
        output=_dict(row["output"]),
        error=_dict(row["error"]),
        started_at=_optional_datetime(row["started_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
    )


def _sleep_from_row(row: RowMapping) -> SleepConsolidationRecord:
    return SleepConsolidationRecord(
        consolidation_id=str(row["consolidation_id"]),
        cycle_run_id=str(row["cycle_run_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        owner_scope=_list_str(row["owner_scope"]),
        working_memory_slots_reviewed=int(row["working_memory_slots_reviewed"]),
        memories_decayed=int(row["memories_decayed"]),
        conflicts_detected=int(row["conflicts_detected"]),
        compaction_runs=int(row["compaction_runs"]),
        reflections_created=int(row["reflections_created"]),
        skill_candidates_created=int(row["skill_candidates_created"]),
        regression_cases_checked=int(row["regression_cases_checked"]),
        visual_snapshots_created=int(row["visual_snapshots_created"]),
        summary=str(row["summary"]),
        result=_dict(row["result"]),
        created_at=_optional_datetime(row["created_at"]),
    )


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _optional_datetime(value: Any) -> datetime | None:
    return _aware(value) if isinstance(value, datetime) else None


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_str(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _list_dict(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [dict(item) for item in value if isinstance(item, dict)]
    return []
