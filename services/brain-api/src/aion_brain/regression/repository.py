"""Persistent repository for golden trace cases and regression runs."""

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
    delete,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.regression import (
    RegressionCase,
    RegressionCaseStatus,
    RegressionResultStatus,
    RegressionRun,
    RegressionRunResult,
    RegressionRunStatus,
)
from aion_brain.contracts.replay import TraceComparison

regression_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_regression_cases = Table(
    "aion_regression_cases",
    regression_metadata,
    Column("case_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("source_trace_id", Text, nullable=False),
    Column("input_snapshot_id", Text, nullable=False),
    Column("expected_snapshot_id", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("tags", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_regression_cases_name", "name"),
    Index("ix_aion_regression_cases_source_trace_id", "source_trace_id"),
    Index("ix_aion_regression_cases_status", "status"),
    Index("ix_aion_regression_cases_created_at", "created_at"),
)

aion_regression_runs = Table(
    "aion_regression_runs",
    regression_metadata,
    Column("regression_run_id", Text, primary_key=True),
    Column("status", Text, nullable=False),
    Column("case_count", Integer, nullable=False),
    Column("passed_count", Integer, nullable=False),
    Column("failed_count", Integer, nullable=False),
    Column("drift_count", Integer, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_regression_runs_status", "status"),
    Index("ix_aion_regression_runs_created_at", "created_at"),
)

aion_regression_run_results = Table(
    "aion_regression_run_results",
    regression_metadata,
    Column("result_id", Text, primary_key=True),
    Column(
        "regression_run_id",
        Text,
        ForeignKey("aion_regression_runs.regression_run_id"),
        nullable=False,
    ),
    Column("case_id", Text, nullable=False),
    Column("replay_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("drift_detected", Boolean, nullable=False),
    Column("comparison", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_regression_run_results_regression_run_id", "regression_run_id"),
    Index("ix_aion_regression_run_results_case_id", "case_id"),
    Index("ix_aion_regression_run_results_replay_id", "replay_id"),
    Index("ix_aion_regression_run_results_status", "status"),
    Index("ix_aion_regression_run_results_drift_detected", "drift_detected"),
    Index("ix_aion_regression_run_results_created_at", "created_at"),
)


class RegressionRepository:
    """Store regression cases, runs, and per-case outcomes."""

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

    def save_case(self, case: RegressionCase) -> RegressionCase:
        """Persist and return a regression case."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = case.model_copy(
            update={"created_at": case.created_at or now, "updated_at": now}
        )
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_regression_cases).where(aion_regression_cases.c.case_id == case.case_id)
            )
            connection.execute(insert(aion_regression_cases).values(**stored.model_dump(mode="python")))
        return stored

    def get_case(self, case_id: str) -> RegressionCase | None:
        """Return a case by ID."""
        self._ensure_schema()
        statement = select(aion_regression_cases).where(aion_regression_cases.c.case_id == case_id)
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_case(row) if row is not None else None

    def list_cases(
        self,
        *,
        status: str | None = None,
        tags: list[str] | None = None,
        limit: int = 50,
    ) -> list[RegressionCase]:
        """Return recent cases with local tag filtering."""
        self._ensure_schema()
        statement = select(aion_regression_cases)
        if status:
            statement = statement.where(aion_regression_cases.c.status == status)
        statement = statement.order_by(aion_regression_cases.c.created_at.desc()).limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        cases = [_row_to_case(row) for row in rows]
        if tags:
            requested = set(tags)
            cases = [case for case in cases if requested & set(case.tags)]
        return cases

    def save_run(self, run: RegressionRun) -> RegressionRun:
        """Persist a run and its result rows."""
        self._ensure_schema()
        stored = run.model_copy(update={"created_at": run.created_at or datetime.now(UTC)})
        values = stored.model_dump(mode="python", exclude={"results"})
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_regression_run_results).where(
                    aion_regression_run_results.c.regression_run_id == stored.regression_run_id
                )
            )
            connection.execute(
                delete(aion_regression_runs).where(
                    aion_regression_runs.c.regression_run_id == stored.regression_run_id
                )
            )
            connection.execute(insert(aion_regression_runs).values(**values))
            for result in stored.results:
                result_values = result.model_dump(mode="python", exclude={"comparison"})
                result_values["comparison"] = result.comparison.model_dump(mode="json")
                result_values["created_at"] = result.created_at or datetime.now(UTC)
                connection.execute(insert(aion_regression_run_results).values(**result_values))
        return stored

    def get_run(self, regression_run_id: str) -> RegressionRun | None:
        """Return a run and its per-case outcomes."""
        self._ensure_schema()
        run_statement = select(aion_regression_runs).where(
            aion_regression_runs.c.regression_run_id == regression_run_id
        )
        result_statement = (
            select(aion_regression_run_results)
            .where(aion_regression_run_results.c.regression_run_id == regression_run_id)
            .order_by(aion_regression_run_results.c.created_at)
        )
        with self._engine.connect() as connection:
            run_row = connection.execute(run_statement).mappings().first()
            result_rows = connection.execute(result_statement).mappings().all()
        if run_row is None:
            return None
        return _row_to_run(run_row, [_row_to_result(row) for row in result_rows])

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        regression_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_case(row: RowMapping) -> RegressionCase:
    return RegressionCase(
        case_id=str(row["case_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        source_trace_id=str(row["source_trace_id"]),
        input_snapshot_id=str(row["input_snapshot_id"]),
        expected_snapshot_id=str(row["expected_snapshot_id"]),
        owner_scope=_string_list(row["owner_scope"]),
        status=cast(RegressionCaseStatus, str(row["status"])),
        tags=_string_list(row["tags"]),
        metadata=dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_datetime(row["updated_at"]),
    )


def _row_to_result(row: RowMapping) -> RegressionRunResult:
    return RegressionRunResult(
        result_id=str(row["result_id"]),
        regression_run_id=str(row["regression_run_id"]),
        case_id=str(row["case_id"]),
        replay_id=_optional_str(row["replay_id"]),
        status=cast(RegressionResultStatus, str(row["status"])),
        drift_detected=bool(row["drift_detected"]),
        comparison=TraceComparison.model_validate(row["comparison"]),
        created_at=_datetime(row["created_at"]),
    )


def _row_to_run(row: RowMapping, results: list[RegressionRunResult]) -> RegressionRun:
    return RegressionRun(
        regression_run_id=str(row["regression_run_id"]),
        status=cast(RegressionRunStatus, str(row["status"])),
        case_count=int(row["case_count"]),
        passed_count=int(row["passed_count"]),
        failed_count=int(row["failed_count"]),
        drift_count=int(row["drift_count"]),
        results=results,
        report=dict(row["report"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError("Expected datetime-compatible value")


def _optional_datetime(value: Any) -> datetime | None:
    return None if value is None else _datetime(value)
