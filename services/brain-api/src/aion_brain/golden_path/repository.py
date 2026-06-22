"""Persistent repository for Golden Path Scenario Harness records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, TypeVar

from pydantic import BaseModel
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    delete,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.golden_path import (
    GoldenPathAssertionResult,
    GoldenPathFixturePack,
    GoldenPathReport,
    GoldenPathRun,
    GoldenPathScenario,
    GoldenPathStepResult,
)

golden_path_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")


aion_golden_path_scenarios = Table(
    "aion_golden_path_scenarios",
    golden_path_metadata,
    Column("golden_path_scenario_id", Text, primary_key=True),
    Column("scenario_key", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("scenario_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("required_services", json_payload_type, nullable=False),
    Column("steps", json_payload_type, nullable=False),
    Column("assertions", json_payload_type, nullable=False),
    Column("tags", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("scenario_key", name="uq_aion_golden_path_scenario_key"),
    Index("ix_aion_golden_path_scenarios_key", "scenario_key"),
    Index("ix_aion_golden_path_scenarios_status", "status"),
    Index("ix_aion_golden_path_scenarios_type", "scenario_type"),
    Index("ix_aion_golden_path_scenarios_created_at", "created_at"),
)

aion_golden_path_fixture_packs = Table(
    "aion_golden_path_fixture_packs",
    golden_path_metadata,
    Column("fixture_pack_id", Text, primary_key=True),
    Column("fixture_pack_key", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("workspace_id", Text, nullable=True),
    Column("fixtures", json_payload_type, nullable=False),
    Column("seeded_resource_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("fixture_pack_key", name="uq_aion_golden_path_fixture_pack_key"),
    Index("ix_aion_golden_path_fixture_packs_key", "fixture_pack_key"),
    Index("ix_aion_golden_path_fixture_packs_status", "status"),
    Index("ix_aion_golden_path_fixture_packs_workspace", "workspace_id"),
    Index("ix_aion_golden_path_fixture_packs_created_at", "created_at"),
)

aion_golden_path_runs = Table(
    "aion_golden_path_runs",
    golden_path_metadata,
    Column("golden_path_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("scenario_ids", json_payload_type, nullable=False),
    Column("fixture_pack_ids", json_payload_type, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("passed_count", Integer, nullable=False),
    Column("failed_count", Integer, nullable=False),
    Column("warning_count", Integer, nullable=False),
    Column("skipped_count", Integer, nullable=False),
    Column("blocked_count", Integer, nullable=False),
    Column("step_result_ids", json_payload_type, nullable=False),
    Column("assertion_result_ids", json_payload_type, nullable=False),
    Column("report_id", Text, nullable=True),
    Column("warnings", json_payload_type, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_golden_path_runs_trace", "trace_id"),
    Index("ix_aion_golden_path_runs_actor", "actor_id"),
    Index("ix_aion_golden_path_runs_workspace", "workspace_id"),
    Index("ix_aion_golden_path_runs_status", "status"),
    Index("ix_aion_golden_path_runs_mode", "mode"),
    Index("ix_aion_golden_path_runs_started_at", "started_at"),
    Index("ix_aion_golden_path_runs_completed_at", "completed_at"),
    Index("ix_aion_golden_path_runs_created_at", "created_at"),
)

aion_golden_path_step_results = Table(
    "aion_golden_path_step_results",
    golden_path_metadata,
    Column("step_result_id", Text, primary_key=True),
    Column(
        "golden_path_run_id",
        Text,
        ForeignKey("aion_golden_path_runs.golden_path_run_id"),
        nullable=False,
    ),
    Column(
        "golden_path_scenario_id",
        Text,
        ForeignKey("aion_golden_path_scenarios.golden_path_scenario_id"),
        nullable=False,
    ),
    Column("trace_id", Text, nullable=True),
    Column("step_key", Text, nullable=False),
    Column("step_order", Integer, nullable=False),
    Column("status", Text, nullable=False),
    Column("service_name", Text, nullable=False),
    Column("action_name", Text, nullable=False),
    Column("input_summary", json_payload_type, nullable=False),
    Column("output_summary", json_payload_type, nullable=False),
    Column("resource_refs", json_payload_type, nullable=False),
    Column("duration_ms", Integer, nullable=True),
    Column("error", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_golden_path_steps_run", "golden_path_run_id"),
    Index("ix_aion_golden_path_steps_scenario", "golden_path_scenario_id"),
    Index("ix_aion_golden_path_steps_key", "step_key"),
    Index("ix_aion_golden_path_steps_order", "step_order"),
    Index("ix_aion_golden_path_steps_status", "status"),
    Index("ix_aion_golden_path_steps_service", "service_name"),
    Index("ix_aion_golden_path_steps_action", "action_name"),
    Index("ix_aion_golden_path_steps_created_at", "created_at"),
)

aion_golden_path_assertion_results = Table(
    "aion_golden_path_assertion_results",
    golden_path_metadata,
    Column("assertion_result_id", Text, primary_key=True),
    Column(
        "golden_path_run_id",
        Text,
        ForeignKey("aion_golden_path_runs.golden_path_run_id"),
        nullable=False,
    ),
    Column(
        "golden_path_scenario_id",
        Text,
        ForeignKey("aion_golden_path_scenarios.golden_path_scenario_id"),
        nullable=False,
    ),
    Column("step_result_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("assertion_key", Text, nullable=False),
    Column("assertion_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("expected", json_payload_type, nullable=False),
    Column("actual", json_payload_type, nullable=False),
    Column("message", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_golden_path_assertions_run", "golden_path_run_id"),
    Index("ix_aion_golden_path_assertions_scenario", "golden_path_scenario_id"),
    Index("ix_aion_golden_path_assertions_step", "step_result_id"),
    Index("ix_aion_golden_path_assertions_key", "assertion_key"),
    Index("ix_aion_golden_path_assertions_type", "assertion_type"),
    Index("ix_aion_golden_path_assertions_status", "status"),
    Index("ix_aion_golden_path_assertions_severity", "severity"),
    Index("ix_aion_golden_path_assertions_created_at", "created_at"),
)

aion_golden_path_reports = Table(
    "aion_golden_path_reports",
    golden_path_metadata,
    Column("golden_path_report_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("golden_path_run_id", Text, nullable=True),
    Column("scenario_count", Integer, nullable=False),
    Column("passed_count", Integer, nullable=False),
    Column("failed_count", Integer, nullable=False),
    Column("warning_count", Integer, nullable=False),
    Column("blocked_count", Integer, nullable=False),
    Column("readiness_score", Float, nullable=False),
    Column("release_candidate_ready", Boolean, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("recommendations", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_golden_path_reports_trace", "trace_id"),
    Index("ix_aion_golden_path_reports_status", "status"),
    Index("ix_aion_golden_path_reports_run", "golden_path_run_id"),
    Index("ix_aion_golden_path_reports_score", "readiness_score"),
    Index("ix_aion_golden_path_reports_ready", "release_candidate_ready"),
    Index("ix_aion_golden_path_reports_created_at", "created_at"),
)

ModelT = TypeVar("ModelT", bound=BaseModel)


class GoldenPathRepository:
    """Store golden path records without mutating non-scenario records."""

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

    def save_scenario(self, scenario: GoldenPathScenario) -> GoldenPathScenario:
        """Persist a scenario definition by key."""
        now = datetime.now(UTC)
        stored = scenario.model_copy(
            update={"created_at": scenario.created_at or now, "updated_at": now}
        )
        self._upsert(
            aion_golden_path_scenarios,
            "golden_path_scenario_id",
            stored.golden_path_scenario_id,
            _values(aion_golden_path_scenarios, stored),
        )
        return stored

    def get_scenario(self, scenario_key: str) -> GoldenPathScenario | None:
        """Return one scenario by scenario key."""
        return self._get(
            aion_golden_path_scenarios, "scenario_key", scenario_key, GoldenPathScenario
        )

    def get_scenario_by_id(self, scenario_id: str) -> GoldenPathScenario | None:
        """Return one scenario by primary id."""
        return self._get(
            aion_golden_path_scenarios,
            "golden_path_scenario_id",
            scenario_id,
            GoldenPathScenario,
        )

    def list_scenarios(
        self,
        *,
        status: str | None = None,
        scenario_type: str | None = None,
        limit: int = 100,
    ) -> list[GoldenPathScenario]:
        """List scenarios."""
        return self._list(
            aion_golden_path_scenarios,
            GoldenPathScenario,
            {"status": status, "scenario_type": scenario_type},
            "created_at",
            limit,
        )

    def save_fixture_pack(self, pack: GoldenPathFixturePack) -> GoldenPathFixturePack:
        """Persist a fixture pack by key."""
        stored = pack.model_copy(update={"created_at": pack.created_at or datetime.now(UTC)})
        self._replace(
            aion_golden_path_fixture_packs,
            "fixture_pack_id",
            stored.fixture_pack_id,
            _values(aion_golden_path_fixture_packs, stored),
        )
        return stored

    def get_fixture_pack(self, fixture_pack_key: str) -> GoldenPathFixturePack | None:
        """Return one fixture pack by key."""
        return self._get(
            aion_golden_path_fixture_packs,
            "fixture_pack_key",
            fixture_pack_key,
            GoldenPathFixturePack,
        )

    def get_fixture_pack_by_id(self, fixture_pack_id: str) -> GoldenPathFixturePack | None:
        """Return one fixture pack by id."""
        return self._get(
            aion_golden_path_fixture_packs,
            "fixture_pack_id",
            fixture_pack_id,
            GoldenPathFixturePack,
        )

    def list_fixture_packs(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[GoldenPathFixturePack]:
        """List fixture packs."""
        return self._list(
            aion_golden_path_fixture_packs,
            GoldenPathFixturePack,
            {"status": status},
            "created_at",
            limit,
        )

    def save_run(self, run: GoldenPathRun) -> GoldenPathRun:
        """Persist a run with step and assertion result rows."""
        stored = run.model_copy(update={"created_at": run.created_at or datetime.now(UTC)})
        self._ensure_schema()
        run_values = _run_values(stored)
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_golden_path_step_results).where(
                    aion_golden_path_step_results.c.golden_path_run_id == stored.golden_path_run_id
                )
            )
            connection.execute(
                delete(aion_golden_path_assertion_results).where(
                    aion_golden_path_assertion_results.c.golden_path_run_id
                    == stored.golden_path_run_id
                )
            )
            connection.execute(
                delete(aion_golden_path_runs).where(
                    aion_golden_path_runs.c.golden_path_run_id == stored.golden_path_run_id
                )
            )
            connection.execute(insert(aion_golden_path_runs).values(**run_values))
            for step in stored.step_results:
                connection.execute(
                    insert(aion_golden_path_step_results).values(
                        **_values(aion_golden_path_step_results, step)
                    )
                )
            for assertion in stored.assertion_results:
                connection.execute(
                    insert(aion_golden_path_assertion_results).values(
                        **_values(aion_golden_path_assertion_results, assertion)
                    )
                )
        return stored

    def get_run(self, golden_path_run_id: str) -> GoldenPathRun | None:
        """Return one run with scenario, fixture, step, and assertion records."""
        self._ensure_schema()
        statement = select(aion_golden_path_runs).where(
            aion_golden_path_runs.c.golden_path_run_id == golden_path_run_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return self._row_to_run(row) if row is not None else None

    def list_runs(
        self,
        *,
        status: str | None = None,
        trace_id: str | None = None,
        limit: int = 50,
    ) -> list[GoldenPathRun]:
        """List runs."""
        self._ensure_schema()
        statement = select(aion_golden_path_runs)
        if status:
            statement = statement.where(aion_golden_path_runs.c.status == status)
        if trace_id:
            statement = statement.where(aion_golden_path_runs.c.trace_id == trace_id)
        statement = statement.order_by(aion_golden_path_runs.c.created_at.desc()).limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [run for row in rows if (run := self._row_to_run(row)) is not None]

    def save_report(self, report: GoldenPathReport) -> GoldenPathReport:
        """Persist a golden path report."""
        stored = report.model_copy(update={"created_at": report.created_at or datetime.now(UTC)})
        self._replace(
            aion_golden_path_reports,
            "golden_path_report_id",
            stored.golden_path_report_id,
            _values(aion_golden_path_reports, stored),
        )
        return stored

    def get_report(self, golden_path_report_id: str) -> GoldenPathReport | None:
        """Return one report."""
        return self._get(
            aion_golden_path_reports,
            "golden_path_report_id",
            golden_path_report_id,
            GoldenPathReport,
        )

    def list_reports(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[GoldenPathReport]:
        """List reports."""
        return self._list(
            aion_golden_path_reports,
            GoldenPathReport,
            {"status": status},
            "created_at",
            limit,
        )

    def latest_run(self) -> GoldenPathRun | None:
        """Return the most recent run."""
        runs = self.list_runs(limit=1)
        return runs[0] if runs else None

    def latest_report(self) -> GoldenPathReport | None:
        """Return the most recent report."""
        reports = self.list_reports(limit=1)
        return reports[0] if reports else None

    def status(self, scope: list[str] | None = None) -> dict[str, Any]:
        """Return a lightweight operator status."""
        latest = self.latest_report()
        latest_run = self.latest_run()
        status = getattr(latest, "status", None) or getattr(latest_run, "status", None) or "warning"
        return {
            "status": status,
            "latest_run_id": getattr(latest_run, "golden_path_run_id", None),
            "latest_report_id": getattr(latest, "golden_path_report_id", None),
            "readiness_score": getattr(latest, "readiness_score", 0.0),
            "scope": scope or [],
        }

    def list_registry_records(self, *, limit: int = 100) -> list[dict[str, Any]]:
        """Return resource-registry-compatible summaries."""
        records: list[dict[str, Any]] = []
        records.extend(
            _registry_record(
                "golden_path_scenario",
                item.golden_path_scenario_id,
                item.scenario_key,
                item.owner_scope,
            )
            for item in self.list_scenarios(limit=limit)
        )
        records.extend(
            _registry_record(
                "golden_path_run",
                item.golden_path_run_id,
                item.status,
                item.owner_scope,
            )
            for item in self.list_runs(limit=limit)
        )
        records.extend(
            _registry_record(
                "golden_path_report",
                item.golden_path_report_id,
                item.status,
                item.owner_scope,
            )
            for item in self.list_reports(limit=limit)
        )
        return records[:limit]

    def _row_to_run(self, row: RowMapping | None) -> GoldenPathRun | None:
        if row is None:
            return None
        scenario_ids = _list(row.get("scenario_ids"))
        fixture_pack_ids = _list(row.get("fixture_pack_ids"))
        scenarios = [
            scenario
            for scenario_id in scenario_ids
            if (scenario := self.get_scenario_by_id(str(scenario_id))) is not None
        ]
        fixture_packs = [
            pack
            for pack_id in fixture_pack_ids
            if (pack := self.get_fixture_pack_by_id(str(pack_id))) is not None
        ]
        steps = self._list_step_results(str(row["golden_path_run_id"]))
        assertions = self._list_assertion_results(str(row["golden_path_run_id"]))
        payload = _payload(row)
        payload.update(
            {
                "scenarios": scenarios,
                "fixture_packs": fixture_packs,
                "step_results": steps,
                "assertion_results": assertions,
            }
        )
        payload.pop("scenario_ids", None)
        payload.pop("fixture_pack_ids", None)
        payload.pop("step_result_ids", None)
        payload.pop("assertion_result_ids", None)
        return GoldenPathRun.model_validate(payload)

    def _list_step_results(self, golden_path_run_id: str) -> list[GoldenPathStepResult]:
        statement = (
            select(aion_golden_path_step_results)
            .where(aion_golden_path_step_results.c.golden_path_run_id == golden_path_run_id)
            .order_by(aion_golden_path_step_results.c.step_order.asc())
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [GoldenPathStepResult.model_validate(_payload(row)) for row in rows]

    def _list_assertion_results(self, golden_path_run_id: str) -> list[GoldenPathAssertionResult]:
        statement = (
            select(aion_golden_path_assertion_results)
            .where(aion_golden_path_assertion_results.c.golden_path_run_id == golden_path_run_id)
            .order_by(aion_golden_path_assertion_results.c.created_at.asc())
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [GoldenPathAssertionResult.model_validate(_payload(row)) for row in rows]

    def _replace(
        self,
        table: Table,
        key: str,
        value: str,
        values: dict[str, Any],
    ) -> None:
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(delete(table).where(getattr(table.c, key) == value))
            connection.execute(insert(table).values(**values))

    def _upsert(
        self,
        table: Table,
        key: str,
        value: str,
        values: dict[str, Any],
    ) -> None:
        self._ensure_schema()
        key_column = getattr(table.c, key)
        with self._engine.begin() as connection:
            existing = connection.execute(select(key_column).where(key_column == value)).first()
            if existing is None:
                connection.execute(insert(table).values(**values))
                return
            connection.execute(update(table).where(key_column == value).values(**values))

    def _get(
        self,
        table: Table,
        key: str,
        value: str,
        model: type[ModelT],
    ) -> ModelT | None:
        self._ensure_schema()
        statement = select(table).where(getattr(table.c, key) == value)
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return model.model_validate(_payload(row)) if row is not None else None

    def _list(
        self,
        table: Table,
        model: type[ModelT],
        filters: dict[str, Any],
        order_column: str,
        limit: int,
    ) -> list[ModelT]:
        self._ensure_schema()
        statement = select(table)
        for key, value in filters.items():
            if value is not None:
                statement = statement.where(getattr(table.c, key) == value)
        statement = statement.order_by(getattr(table.c, order_column).desc()).limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [model.model_validate(_payload(row)) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        golden_path_metadata.create_all(self._engine)
        self._schema_ready = True


def _values(table: Table, model: BaseModel) -> dict[str, Any]:
    json_payload = model.model_dump(mode="json")
    python_payload = model.model_dump(mode="python")
    result: dict[str, Any] = {}
    for column in table.c:
        name = column.name
        if name not in json_payload:
            continue
        if isinstance(column.type, DateTime):
            result[name] = python_payload.get(name)
        else:
            result[name] = json_payload.get(name)
    return result


def _run_values(run: GoldenPathRun) -> dict[str, Any]:
    payload = run.model_dump(mode="json")
    python_payload = run.model_dump(mode="python")
    payload["scenario_ids"] = [scenario.golden_path_scenario_id for scenario in run.scenarios]
    payload["fixture_pack_ids"] = [pack.fixture_pack_id for pack in run.fixture_packs]
    payload["step_result_ids"] = [step.step_result_id for step in run.step_results]
    payload["assertion_result_ids"] = [
        assertion.assertion_result_id for assertion in run.assertion_results
    ]
    for key in ("scenarios", "fixture_packs", "step_results", "assertion_results"):
        payload.pop(key, None)
    for key in ("started_at", "completed_at", "created_at"):
        payload[key] = python_payload.get(key)
    return {column.name: payload.get(column.name) for column in aion_golden_path_runs.c}


def _payload(row: RowMapping | None) -> dict[str, Any]:
    return dict(row or {})


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _registry_record(
    resource_type: str,
    resource_id: str,
    label: str,
    scope: list[str],
) -> dict[str, Any]:
    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "resource_uri": f"aion://{resource_type}/{resource_id}",
        "label": label,
        "owner_scope": scope,
        "metadata": {"source": "golden_path"},
    }


__all__ = [
    "GoldenPathRepository",
    "aion_golden_path_assertion_results",
    "aion_golden_path_fixture_packs",
    "aion_golden_path_reports",
    "aion_golden_path_runs",
    "aion_golden_path_scenarios",
    "aion_golden_path_step_results",
    "golden_path_metadata",
]
