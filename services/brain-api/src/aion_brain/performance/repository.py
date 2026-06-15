"""Persistence for local performance benchmark records."""

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
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.performance import (
    BenchmarkDefinition,
    BenchmarkRun,
    BenchmarkRunMode,
    BenchmarkRunStatus,
    BenchmarkType,
    CapacityBaseline,
    CapacityBaselineStatus,
    PerformanceRegressionReport,
    PerformanceSample,
    PerformanceSampleStatus,
    ResourceBudgetProfile,
)

performance_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_performance_samples = Table(
    "aion_performance_samples",
    performance_metadata,
    Column("performance_sample_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("benchmark_run_id", Text, nullable=True),
    Column("operation_type", Text, nullable=False),
    Column("component", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("duration_ms", Integer, nullable=False),
    Column("input_size_bytes", Integer, nullable=True),
    Column("output_size_bytes", Integer, nullable=True),
    Column("item_count", Integer, nullable=True),
    Column("error", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_performance_samples_benchmark_run_id", "benchmark_run_id"),
    Index("ix_aion_performance_samples_trace_id", "trace_id"),
    Index("ix_aion_performance_samples_operation_type", "operation_type"),
    Index("ix_aion_performance_samples_component", "component"),
    Index("ix_aion_performance_samples_status", "status"),
    Index("ix_aion_performance_samples_duration_ms", "duration_ms"),
    Index("ix_aion_performance_samples_created_at", "created_at"),
)

aion_benchmark_definitions = Table(
    "aion_benchmark_definitions",
    performance_metadata,
    Column("benchmark_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("benchmark_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("steps", json_payload_type, nullable=False),
    Column("thresholds", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_benchmark_definitions_name", "name"),
    Index("ix_aion_benchmark_definitions_status", "status"),
    Index("ix_aion_benchmark_definitions_benchmark_type", "benchmark_type"),
    Index("ix_aion_benchmark_definitions_created_at", "created_at"),
)

aion_benchmark_runs = Table(
    "aion_benchmark_runs",
    performance_metadata,
    Column("benchmark_run_id", Text, primary_key=True),
    Column("benchmark_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("sample_count", Integer, nullable=False),
    Column("passed_count", Integer, nullable=False),
    Column("failed_count", Integer, nullable=False),
    Column("warning_count", Integer, nullable=False),
    Column("summary", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_benchmark_runs_benchmark_id", "benchmark_id"),
    Index("ix_aion_benchmark_runs_trace_id", "trace_id"),
    Index("ix_aion_benchmark_runs_actor_id", "actor_id"),
    Index("ix_aion_benchmark_runs_workspace_id", "workspace_id"),
    Index("ix_aion_benchmark_runs_status", "status"),
    Index("ix_aion_benchmark_runs_mode", "mode"),
    Index("ix_aion_benchmark_runs_created_at", "created_at"),
)

aion_capacity_baselines = Table(
    "aion_capacity_baselines",
    performance_metadata,
    Column("capacity_baseline_id", Text, primary_key=True),
    Column("version", Text, nullable=False),
    Column("baseline_name", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("environment", json_payload_type, nullable=False),
    Column("metrics", json_payload_type, nullable=False),
    Column("thresholds", json_payload_type, nullable=False),
    Column("benchmark_run_ids", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_capacity_baselines_version", "version"),
    Index("ix_aion_capacity_baselines_baseline_name", "baseline_name"),
    Index("ix_aion_capacity_baselines_status", "status"),
    Index("ix_aion_capacity_baselines_created_at", "created_at"),
)

aion_resource_budget_profiles = Table(
    "aion_resource_budget_profiles",
    performance_metadata,
    Column("resource_budget_profile_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("budgets", json_payload_type, nullable=False),
    Column("enforcement_mode", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_resource_budget_profiles_name", "name"),
    Index("ix_aion_resource_budget_profiles_status", "status"),
    Index("ix_aion_resource_budget_profiles_enforcement_mode", "enforcement_mode"),
    Index("ix_aion_resource_budget_profiles_created_at", "created_at"),
)

aion_performance_regression_reports = Table(
    "aion_performance_regression_reports",
    performance_metadata,
    Column("regression_report_id", Text, primary_key=True),
    Column("baseline_id", Text, nullable=True),
    Column("benchmark_run_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("regressions", json_payload_type, nullable=False),
    Column("improvements", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_performance_regression_reports_baseline_id", "baseline_id"),
    Index("ix_aion_performance_regression_reports_benchmark_run_id", "benchmark_run_id"),
    Index("ix_aion_performance_regression_reports_status", "status"),
    Index("ix_aion_performance_regression_reports_created_at", "created_at"),
)


class PerformanceRepository:
    """Store local performance records."""

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
            if database_url.startswith("sqlite") and ":memory:" in database_url:
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

    def save_sample(self, sample: PerformanceSample) -> PerformanceSample:
        self._ensure_schema()
        values = sample.model_dump(mode="json", exclude={"created_at"})
        values["created_at"] = sample.created_at or datetime.now(UTC)
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_performance_samples).where(
                    aion_performance_samples.c.performance_sample_id
                    == sample.performance_sample_id
                )
            )
            connection.execute(insert(aion_performance_samples).values(**values))
        return sample.model_copy(update={"created_at": values["created_at"]})

    def list_samples(
        self,
        *,
        operation_type: str | None = None,
        benchmark_run_id: str | None = None,
        limit: int | None = None,
    ) -> list[PerformanceSample]:
        self._ensure_schema()
        statement = select(aion_performance_samples)
        if operation_type:
            statement = statement.where(aion_performance_samples.c.operation_type == operation_type)
        if benchmark_run_id:
            statement = statement.where(
                aion_performance_samples.c.benchmark_run_id == benchmark_run_id
            )
        statement = statement.order_by(aion_performance_samples.c.created_at.desc())
        if limit:
            statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_sample(row) for row in rows]

    def save_benchmark(self, definition: BenchmarkDefinition) -> BenchmarkDefinition:
        self._ensure_schema()
        now = datetime.now(UTC)
        saved = definition.model_copy(
            update={
                "created_at": definition.created_at or now,
                "updated_at": now,
            }
        )
        values = saved.model_dump(mode="json", exclude={"created_at", "updated_at", "disabled_at"})
        values["created_at"] = saved.created_at
        values["updated_at"] = saved.updated_at
        values["disabled_at"] = saved.disabled_at
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_benchmark_definitions).where(
                    aion_benchmark_definitions.c.benchmark_id == saved.benchmark_id
                )
            )
            connection.execute(insert(aion_benchmark_definitions).values(**values))
        return saved

    def get_benchmark(self, benchmark_id: str) -> BenchmarkDefinition | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_benchmark_definitions).where(
                    aion_benchmark_definitions.c.benchmark_id == benchmark_id
                )
            ).mappings().first()
        return _row_to_benchmark(row) if row is not None else None

    def list_benchmarks(
        self,
        *,
        status: str | None = None,
        benchmark_type: str | None = None,
    ) -> list[BenchmarkDefinition]:
        self._ensure_schema()
        statement = select(aion_benchmark_definitions)
        if status:
            statement = statement.where(aion_benchmark_definitions.c.status == status)
        if benchmark_type:
            statement = statement.where(
                aion_benchmark_definitions.c.benchmark_type == benchmark_type
            )
        statement = statement.order_by(aion_benchmark_definitions.c.created_at.desc())
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_benchmark(row) for row in rows]

    def save_run(self, run: BenchmarkRun) -> BenchmarkRun:
        self._ensure_schema()
        values = run.model_dump(
            mode="json",
            exclude={"samples", "created_at", "completed_at"},
        )
        values["created_at"] = run.created_at or datetime.now(UTC)
        values["completed_at"] = run.completed_at
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_benchmark_runs).where(
                    aion_benchmark_runs.c.benchmark_run_id == run.benchmark_run_id
                )
            )
            connection.execute(insert(aion_benchmark_runs).values(**values))
        for sample in run.samples:
            self.save_sample(sample)
        return run.model_copy(update={"created_at": values["created_at"]})

    def get_run(self, benchmark_run_id: str) -> BenchmarkRun | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_benchmark_runs).where(
                    aion_benchmark_runs.c.benchmark_run_id == benchmark_run_id
                )
            ).mappings().first()
        if row is None:
            return None
        samples = self.list_samples(benchmark_run_id=benchmark_run_id)
        return _row_to_run(row, samples)

    def list_runs(
        self,
        *,
        status: str | None = None,
        benchmark_type: str | None = None,
        limit: int = 50,
    ) -> list[BenchmarkRun]:
        self._ensure_schema()
        statement = select(aion_benchmark_runs)
        if status:
            statement = statement.where(aion_benchmark_runs.c.status == status)
        statement = statement.order_by(aion_benchmark_runs.c.created_at.desc()).limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        runs = [run for row in rows if (run := self.get_run(str(row["benchmark_run_id"])))]
        if benchmark_type:
            ids = {
                item.benchmark_id
                for item in self.list_benchmarks(benchmark_type=benchmark_type)
            }
            runs = [run for run in runs if run.benchmark_id in ids]
        return runs

    def save_baseline(self, baseline: CapacityBaseline) -> CapacityBaseline:
        self._ensure_schema()
        saved = baseline.model_copy(update={"created_at": baseline.created_at or datetime.now(UTC)})
        values = saved.model_dump(mode="json", exclude={"created_at"})
        values["created_at"] = saved.created_at
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_capacity_baselines).where(
                    aion_capacity_baselines.c.capacity_baseline_id
                    == saved.capacity_baseline_id
                )
            )
            connection.execute(insert(aion_capacity_baselines).values(**values))
        return saved

    def get_baseline(self, capacity_baseline_id: str) -> CapacityBaseline | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_capacity_baselines).where(
                    aion_capacity_baselines.c.capacity_baseline_id == capacity_baseline_id
                )
            ).mappings().first()
        return _row_to_baseline(row) if row is not None else None

    def list_baselines(
        self,
        *,
        version: str | None = None,
        status: str | None = None,
    ) -> list[CapacityBaseline]:
        self._ensure_schema()
        statement = select(aion_capacity_baselines)
        if version:
            statement = statement.where(aion_capacity_baselines.c.version == version)
        if status:
            statement = statement.where(aion_capacity_baselines.c.status == status)
        statement = statement.order_by(aion_capacity_baselines.c.created_at.desc())
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_baseline(row) for row in rows]

    def save_budget_profile(self, profile: ResourceBudgetProfile) -> ResourceBudgetProfile:
        self._ensure_schema()
        now = datetime.now(UTC)
        saved = profile.model_copy(
            update={"created_at": profile.created_at or now, "updated_at": now}
        )
        values = saved.model_dump(mode="json", exclude={"created_at", "updated_at", "disabled_at"})
        values["created_at"] = saved.created_at
        values["updated_at"] = saved.updated_at
        values["disabled_at"] = saved.disabled_at
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_resource_budget_profiles).where(
                    aion_resource_budget_profiles.c.resource_budget_profile_id
                    == saved.resource_budget_profile_id
                )
            )
            connection.execute(insert(aion_resource_budget_profiles).values(**values))
        return saved

    def list_budget_profiles(self, *, status: str | None = None) -> list[ResourceBudgetProfile]:
        self._ensure_schema()
        statement = select(aion_resource_budget_profiles)
        if status:
            statement = statement.where(aion_resource_budget_profiles.c.status == status)
        statement = statement.order_by(aion_resource_budget_profiles.c.created_at.desc())
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_budget(row) for row in rows]

    def save_regression_report(
        self,
        report: PerformanceRegressionReport,
    ) -> PerformanceRegressionReport:
        self._ensure_schema()
        saved = report.model_copy(update={"created_at": report.created_at or datetime.now(UTC)})
        values = saved.model_dump(mode="json", exclude={"created_at"})
        values["created_at"] = saved.created_at
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_performance_regression_reports).where(
                    aion_performance_regression_reports.c.regression_report_id
                    == saved.regression_report_id
                )
            )
            connection.execute(insert(aion_performance_regression_reports).values(**values))
        return saved

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        performance_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_sample(row: RowMapping) -> PerformanceSample:
    return PerformanceSample(
        performance_sample_id=str(row["performance_sample_id"]),
        trace_id=_optional_str(row["trace_id"]),
        benchmark_run_id=_optional_str(row["benchmark_run_id"]),
        operation_type=cast(Any, str(row["operation_type"])),
        component=str(row["component"]),
        status=cast(PerformanceSampleStatus, str(row["status"])),
        duration_ms=int(row["duration_ms"]),
        input_size_bytes=_optional_int(row["input_size_bytes"]),
        output_size_bytes=_optional_int(row["output_size_bytes"]),
        item_count=_optional_int(row["item_count"]),
        error=dict(row["error"]),
        metadata=dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
    )


def _row_to_benchmark(row: RowMapping) -> BenchmarkDefinition:
    return BenchmarkDefinition(
        benchmark_id=str(row["benchmark_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(Any, str(row["status"])),
        benchmark_type=cast(BenchmarkType, str(row["benchmark_type"])),
        owner_scope=_string_list(row["owner_scope"]),
        steps=list(row["steps"]),
        thresholds=dict(row["thresholds"]),
        metadata=dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _row_to_run(row: RowMapping, samples: list[PerformanceSample]) -> BenchmarkRun:
    return BenchmarkRun(
        benchmark_run_id=str(row["benchmark_run_id"]),
        benchmark_id=_optional_str(row["benchmark_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        status=cast(BenchmarkRunStatus, str(row["status"])),
        mode=cast(BenchmarkRunMode, str(row["mode"])),
        owner_scope=_string_list(row["owner_scope"]),
        samples=samples,
        sample_count=int(row["sample_count"]),
        passed_count=int(row["passed_count"]),
        failed_count=int(row["failed_count"]),
        warning_count=int(row["warning_count"]),
        summary=dict(row["summary"]),
        report=dict(row["report"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _row_to_baseline(row: RowMapping) -> CapacityBaseline:
    return CapacityBaseline(
        capacity_baseline_id=str(row["capacity_baseline_id"]),
        version=str(row["version"]),
        baseline_name=str(row["baseline_name"]),
        status=cast(CapacityBaselineStatus, str(row["status"])),
        environment=dict(row["environment"]),
        metrics=dict(row["metrics"]),
        thresholds=dict(row["thresholds"]),
        benchmark_run_ids=[str(item) for item in _list(row["benchmark_run_ids"])],
        report=dict(row["report"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
    )


def _row_to_budget(row: RowMapping) -> ResourceBudgetProfile:
    return ResourceBudgetProfile(
        resource_budget_profile_id=str(row["resource_budget_profile_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(Any, str(row["status"])),
        owner_scope=_string_list(row["owner_scope"]),
        budgets=dict(row["budgets"]),
        enforcement_mode=cast(Any, str(row["enforcement_mode"])),
        metadata=dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


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


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _string_list(value: object) -> list[str]:
    return [str(item) for item in _list(value)]
