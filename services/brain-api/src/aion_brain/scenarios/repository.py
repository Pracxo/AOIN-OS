"""Persistence for scenario definitions, runs, step runs, and demo fixtures."""

from datetime import UTC, datetime
from typing import cast

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
    delete,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.scenarios import (
    DemoFixture,
    DemoFixtureStatus,
    DemoFixtureType,
    ScenarioDefinition,
    ScenarioRun,
    ScenarioRunMode,
    ScenarioRunStatus,
    ScenarioStatus,
    ScenarioStep,
    ScenarioStepRun,
    ScenarioStepRunStatus,
    ScenarioStepType,
    ScenarioType,
)

scenario_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_scenario_definitions = Table(
    "aion_scenario_definitions",
    scenario_metadata,
    Column("scenario_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("scenario_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("steps", json_payload_type, nullable=False),
    Column("expected", json_payload_type, nullable=False),
    Column("tags", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_scenario_definitions_name", "name"),
    Index("ix_aion_scenario_definitions_status", "status"),
    Index("ix_aion_scenario_definitions_scenario_type", "scenario_type"),
    Index("ix_aion_scenario_definitions_created_at", "created_at"),
)

aion_scenario_runs = Table(
    "aion_scenario_runs",
    scenario_metadata,
    Column("scenario_run_id", Text, primary_key=True),
    Column("scenario_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("step_count", Integer, nullable=False),
    Column("passed_steps", Integer, nullable=False),
    Column("failed_steps", Integer, nullable=False),
    Column("skipped_steps", Integer, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("comparison", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_scenario_runs_scenario_id", "scenario_id"),
    Index("ix_aion_scenario_runs_trace_id", "trace_id"),
    Index("ix_aion_scenario_runs_actor_id", "actor_id"),
    Index("ix_aion_scenario_runs_workspace_id", "workspace_id"),
    Index("ix_aion_scenario_runs_status", "status"),
    Index("ix_aion_scenario_runs_mode", "mode"),
    Index("ix_aion_scenario_runs_created_at", "created_at"),
)

aion_scenario_step_runs = Table(
    "aion_scenario_step_runs",
    scenario_metadata,
    Column("scenario_step_run_id", Text, primary_key=True),
    Column(
        "scenario_run_id",
        Text,
        ForeignKey("aion_scenario_runs.scenario_run_id"),
        nullable=False,
    ),
    Column("step_id", Text, nullable=False),
    Column("step_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("input", json_payload_type, nullable=False),
    Column("output", json_payload_type, nullable=False),
    Column("expected", json_payload_type, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("duration_ms", Integer, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_scenario_step_runs_scenario_run_id", "scenario_run_id"),
    Index("ix_aion_scenario_step_runs_step_id", "step_id"),
    Index("ix_aion_scenario_step_runs_step_type", "step_type"),
    Index("ix_aion_scenario_step_runs_status", "status"),
    Index("ix_aion_scenario_step_runs_created_at", "created_at"),
)

aion_demo_fixture_records = Table(
    "aion_demo_fixture_records",
    scenario_metadata,
    Column("fixture_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("fixture_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("content", json_payload_type, nullable=False),
    Column("loaded", Boolean, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("loaded_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_demo_fixture_records_name", "name"),
    Index("ix_aion_demo_fixture_records_status", "status"),
    Index("ix_aion_demo_fixture_records_fixture_type", "fixture_type"),
    Index("ix_aion_demo_fixture_records_loaded", "loaded"),
    Index("ix_aion_demo_fixture_records_created_at", "created_at"),
)


class ScenarioRepository:
    """Store scenario definitions, scenario runs, and demo fixture records."""

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
            self._engine = create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_definition(self, scenario: ScenarioDefinition) -> ScenarioDefinition:
        """Persist a scenario definition."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = scenario.model_copy(
            update={"created_at": scenario.created_at or now, "updated_at": now}
        )
        values = stored.model_dump(mode="python", exclude={"steps"})
        values["steps"] = [step.model_dump(mode="json") for step in stored.steps]
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_scenario_definitions).where(
                    aion_scenario_definitions.c.scenario_id == stored.scenario_id
                )
            )
            connection.execute(insert(aion_scenario_definitions).values(**values))
        return stored

    def get_definition(self, scenario_id: str) -> ScenarioDefinition | None:
        """Return one scenario definition."""
        self._ensure_schema()
        statement = select(aion_scenario_definitions).where(
            aion_scenario_definitions.c.scenario_id == scenario_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_definition(row) if row is not None else None

    def list_definitions(
        self,
        *,
        status: str | None = None,
        scenario_type: str | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
    ) -> list[ScenarioDefinition]:
        """Return scenario definitions with local tag filtering."""
        self._ensure_schema()
        statement = select(aion_scenario_definitions)
        if status:
            statement = statement.where(aion_scenario_definitions.c.status == status)
        if scenario_type:
            statement = statement.where(aion_scenario_definitions.c.scenario_type == scenario_type)
        statement = statement.order_by(aion_scenario_definitions.c.created_at.desc()).limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        scenarios = [_row_to_definition(row) for row in rows]
        if tags:
            requested = set(tags)
            scenarios = [scenario for scenario in scenarios if requested & set(scenario.tags)]
        return scenarios

    def save_run(self, run: ScenarioRun) -> ScenarioRun:
        """Persist a scenario run and step results."""
        self._ensure_schema()
        stored = run.model_copy(update={"created_at": run.created_at or datetime.now(UTC)})
        values = stored.model_dump(mode="python", exclude={"steps"})
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_scenario_step_runs).where(
                    aion_scenario_step_runs.c.scenario_run_id == stored.scenario_run_id
                )
            )
            connection.execute(
                delete(aion_scenario_runs).where(
                    aion_scenario_runs.c.scenario_run_id == stored.scenario_run_id
                )
            )
            connection.execute(insert(aion_scenario_runs).values(**values))
            for step in stored.steps:
                connection.execute(
                    insert(aion_scenario_step_runs).values(**step.model_dump(mode="python"))
                )
        return stored

    def get_run(self, scenario_run_id: str) -> ScenarioRun | None:
        """Return a scenario run with step rows."""
        self._ensure_schema()
        run_statement = select(aion_scenario_runs).where(
            aion_scenario_runs.c.scenario_run_id == scenario_run_id
        )
        steps_statement = (
            select(aion_scenario_step_runs)
            .where(aion_scenario_step_runs.c.scenario_run_id == scenario_run_id)
            .order_by(aion_scenario_step_runs.c.created_at)
        )
        with self._engine.connect() as connection:
            run_row = connection.execute(run_statement).mappings().first()
            step_rows = connection.execute(steps_statement).mappings().all()
        if run_row is None:
            return None
        return _row_to_run(run_row, [_row_to_step_run(row) for row in step_rows])

    def list_runs(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[ScenarioRun]:
        """Return recent scenario runs in scope."""
        self._ensure_schema()
        statement = select(aion_scenario_runs)
        if status:
            statement = statement.where(aion_scenario_runs.c.status == status)
        statement = statement.order_by(aion_scenario_runs.c.created_at.desc()).limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        runs = [_row_to_run(row, []) for row in rows]
        return [run for run in runs if set(scope) & set(run.owner_scope)]

    def save_fixture(self, fixture: DemoFixture) -> DemoFixture:
        """Persist a demo fixture record."""
        self._ensure_schema()
        stored = fixture.model_copy(update={"created_at": fixture.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_demo_fixture_records).where(
                    aion_demo_fixture_records.c.fixture_id == stored.fixture_id
                )
            )
            connection.execute(
                insert(aion_demo_fixture_records).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_fixture(self, fixture_id: str) -> DemoFixture | None:
        """Return one fixture record."""
        self._ensure_schema()
        statement = select(aion_demo_fixture_records).where(
            aion_demo_fixture_records.c.fixture_id == fixture_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_fixture(row) if row is not None else None

    def list_fixtures(
        self,
        *,
        scope: list[str],
        fixture_type: str | None = None,
        loaded: bool | None = None,
        limit: int = 100,
    ) -> list[DemoFixture]:
        """Return fixture records with simple scope filtering."""
        self._ensure_schema()
        statement = select(aion_demo_fixture_records)
        if fixture_type:
            statement = statement.where(aion_demo_fixture_records.c.fixture_type == fixture_type)
        if loaded is not None:
            statement = statement.where(aion_demo_fixture_records.c.loaded == loaded)
        statement = statement.order_by(aion_demo_fixture_records.c.created_at.desc()).limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        fixtures = [_row_to_fixture(row) for row in rows]
        return [fixture for fixture in fixtures if set(scope) & set(fixture.owner_scope)]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        scenario_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_definition(row: RowMapping) -> ScenarioDefinition:
    return ScenarioDefinition(
        scenario_id=str(row["scenario_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(ScenarioStatus, str(row["status"])),
        scenario_type=cast(ScenarioType, str(row["scenario_type"])),
        owner_scope=_string_list(row["owner_scope"]),
        steps=[ScenarioStep.model_validate(step) for step in _list(row["steps"])],
        expected=dict(row["expected"]),
        tags=_string_list(row["tags"]),
        metadata=dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _row_to_run(row: RowMapping, steps: list[ScenarioStepRun]) -> ScenarioRun:
    return ScenarioRun(
        scenario_run_id=str(row["scenario_run_id"]),
        scenario_id=_optional_str(row["scenario_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        status=cast(ScenarioRunStatus, str(row["status"])),
        mode=cast(ScenarioRunMode, str(row["mode"])),
        owner_scope=_string_list(row["owner_scope"]),
        step_count=int(row["step_count"]),
        passed_steps=int(row["passed_steps"]),
        failed_steps=int(row["failed_steps"]),
        skipped_steps=int(row["skipped_steps"]),
        steps=steps,
        result=dict(row["result"]),
        comparison=dict(row["comparison"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _row_to_step_run(row: RowMapping) -> ScenarioStepRun:
    return ScenarioStepRun(
        scenario_step_run_id=str(row["scenario_step_run_id"]),
        scenario_run_id=str(row["scenario_run_id"]),
        step_id=str(row["step_id"]),
        step_type=cast(ScenarioStepType, str(row["step_type"])),
        status=cast(ScenarioStepRunStatus, str(row["status"])),
        input=dict(row["input"]),
        output=dict(row["output"]),
        expected=dict(row["expected"]),
        error=dict(row["error"]),
        duration_ms=_optional_int(row["duration_ms"]),
        created_at=_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _row_to_fixture(row: RowMapping) -> DemoFixture:
    return DemoFixture(
        fixture_id=str(row["fixture_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(DemoFixtureStatus, str(row["status"])),
        fixture_type=cast(DemoFixtureType, str(row["fixture_type"])),
        owner_scope=_string_list(row["owner_scope"]),
        content=dict(row["content"]),
        loaded=bool(row["loaded"]),
        result=dict(row["result"]),
        created_at=_datetime(row["created_at"]),
        loaded_at=_optional_datetime(row["loaded_at"]),
    )


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    return int(str(value))


def _datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _optional_datetime(value: object) -> datetime | None:
    return None if value is None else _datetime(value)


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []
