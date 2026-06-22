"""Persistent repository for first-run bootstrap records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.bootstrap import (
    BootstrapProfile,
    BootstrapRun,
    SeedBundle,
    SeedExecutionRecord,
)
from aion_brain.contracts.setup_doctor import SetupFinding, SetupReport

bootstrap_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")


aion_bootstrap_profiles = Table(
    "aion_bootstrap_profiles",
    bootstrap_metadata,
    Column("bootstrap_profile_id", Text, primary_key=True),
    Column("profile_key", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("profile_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("required_services", json_payload_type, nullable=False),
    Column("required_settings", json_payload_type, nullable=False),
    Column("seed_bundle_keys", json_payload_type, nullable=False),
    Column("checks", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("profile_key", name="uq_aion_bootstrap_profiles_key"),
    Index("ix_aion_bootstrap_profiles_key", "profile_key"),
    Index("ix_aion_bootstrap_profiles_status", "status"),
    Index("ix_aion_bootstrap_profiles_type", "profile_type"),
    Index("ix_aion_bootstrap_profiles_created_at", "created_at"),
)

aion_seed_bundles = Table(
    "aion_seed_bundles",
    bootstrap_metadata,
    Column("seed_bundle_id", Text, primary_key=True),
    Column("seed_bundle_key", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("bundle_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("seed_steps", json_payload_type, nullable=False),
    Column("idempotency_keys", json_payload_type, nullable=False),
    Column("dependencies", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("seed_bundle_key", name="uq_aion_seed_bundles_key"),
    Index("ix_aion_seed_bundles_key", "seed_bundle_key"),
    Index("ix_aion_seed_bundles_status", "status"),
    Index("ix_aion_seed_bundles_type", "bundle_type"),
    Index("ix_aion_seed_bundles_created_at", "created_at"),
)

aion_seed_execution_records = Table(
    "aion_seed_execution_records",
    bootstrap_metadata,
    Column("seed_execution_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("seed_bundle_id", Text, nullable=False),
    Column("seed_bundle_key", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("steps_attempted", Integer, nullable=False),
    Column("steps_completed", Integer, nullable=False),
    Column("steps_skipped", Integer, nullable=False),
    Column("steps_failed", Integer, nullable=False),
    Column("created_resource_refs", json_payload_type, nullable=False),
    Column("skipped_resource_refs", json_payload_type, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_seed_execution_trace", "trace_id"),
    Index("ix_aion_seed_execution_actor", "actor_id"),
    Index("ix_aion_seed_execution_workspace", "workspace_id"),
    Index("ix_aion_seed_execution_bundle_id", "seed_bundle_id"),
    Index("ix_aion_seed_execution_bundle_key", "seed_bundle_key"),
    Index("ix_aion_seed_execution_status", "status"),
    Index("ix_aion_seed_execution_mode", "mode"),
    Index("ix_aion_seed_execution_created_at", "created_at"),
)

aion_setup_findings = Table(
    "aion_setup_findings",
    bootstrap_metadata,
    Column("setup_finding_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("finding_type", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("check_key", Text, nullable=False),
    Column("expected", json_payload_type, nullable=False),
    Column("actual", json_payload_type, nullable=False),
    Column("recommended_action", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Column("dismissed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_setup_findings_trace", "trace_id"),
    Index("ix_aion_setup_findings_type", "finding_type"),
    Index("ix_aion_setup_findings_category", "category"),
    Index("ix_aion_setup_findings_severity", "severity"),
    Index("ix_aion_setup_findings_status", "status"),
    Index("ix_aion_setup_findings_check_key", "check_key"),
    Index("ix_aion_setup_findings_created_at", "created_at"),
)

aion_bootstrap_runs = Table(
    "aion_bootstrap_runs",
    bootstrap_metadata,
    Column("bootstrap_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("bootstrap_profile_id", Text, nullable=True),
    Column("profile_key", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("checks_run", json_payload_type, nullable=False),
    Column("seed_execution_ids", json_payload_type, nullable=False),
    Column("setup_finding_ids", json_payload_type, nullable=False),
    Column("golden_path_run_id", Text, nullable=True),
    Column("release_smoke_ref", Text, nullable=True),
    Column("readiness_score", Float, nullable=False),
    Column("local_ready", Boolean, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_bootstrap_runs_trace", "trace_id"),
    Index("ix_aion_bootstrap_runs_actor", "actor_id"),
    Index("ix_aion_bootstrap_runs_workspace", "workspace_id"),
    Index("ix_aion_bootstrap_runs_profile_id", "bootstrap_profile_id"),
    Index("ix_aion_bootstrap_runs_profile_key", "profile_key"),
    Index("ix_aion_bootstrap_runs_status", "status"),
    Index("ix_aion_bootstrap_runs_mode", "mode"),
    Index("ix_aion_bootstrap_runs_score", "readiness_score"),
    Index("ix_aion_bootstrap_runs_local_ready", "local_ready"),
    Index("ix_aion_bootstrap_runs_created_at", "created_at"),
)

aion_setup_reports = Table(
    "aion_setup_reports",
    bootstrap_metadata,
    Column("setup_report_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("bootstrap_run_id", Text, nullable=True),
    Column("readiness_score", Float, nullable=False),
    Column("local_ready", Boolean, nullable=False),
    Column("health_ready", Boolean, nullable=False),
    Column("policy_ready", Boolean, nullable=False),
    Column("sdk_ready", Boolean, nullable=False),
    Column("cli_ready", Boolean, nullable=False),
    Column("golden_path_ready", Boolean, nullable=False),
    Column("release_smoke_ready", Boolean, nullable=False),
    Column("docker_ready", Boolean, nullable=False),
    Column("finding_count", Integer, nullable=False),
    Column("critical_count", Integer, nullable=False),
    Column("warning_count", Integer, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("recommendations", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_setup_reports_trace", "trace_id"),
    Index("ix_aion_setup_reports_status", "status"),
    Index("ix_aion_setup_reports_bootstrap_run", "bootstrap_run_id"),
    Index("ix_aion_setup_reports_score", "readiness_score"),
    Index("ix_aion_setup_reports_local_ready", "local_ready"),
    Index("ix_aion_setup_reports_critical", "critical_count"),
    Index("ix_aion_setup_reports_warning", "warning_count"),
    Index("ix_aion_setup_reports_created_at", "created_at"),
)


class BootstrapRepository:
    """SQLAlchemy-backed bootstrap repository."""

    def __init__(self, database_url: str, *, auto_create: bool = True) -> None:
        connect_args: dict[str, Any] = {}
        poolclass: type[StaticPool] | type[QueuePool] = QueuePool
        if database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
            poolclass = StaticPool
        self._engine = create_engine(database_url, connect_args=connect_args, poolclass=poolclass)
        self._auto_create = auto_create
        self._schema_ready = False

    def save_profile(self, profile: BootstrapProfile) -> BootstrapProfile:
        self._ensure_schema()
        stored = _with_timestamps(profile, created=True)
        with self._engine.begin() as conn:
            _upsert(
                conn,
                aion_bootstrap_profiles,
                "bootstrap_profile_id",
                stored.bootstrap_profile_id,
                _values(aion_bootstrap_profiles, stored),
            )
        return stored

    def get_profile(self, profile_key: str) -> BootstrapProfile | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_bootstrap_profiles).where(
                        aion_bootstrap_profiles.c.profile_key == profile_key
                    )
                )
                .mappings()
                .first()
            )
        return _model_or_none(BootstrapProfile, row)

    def list_profiles(
        self,
        *,
        status: str | None = None,
        profile_type: str | None = None,
        limit: int = 100,
    ) -> list[BootstrapProfile]:
        self._ensure_schema()
        query = (
            select(aion_bootstrap_profiles)
            .order_by(aion_bootstrap_profiles.c.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            query = query.where(aion_bootstrap_profiles.c.status == status)
        if profile_type is not None:
            query = query.where(aion_bootstrap_profiles.c.profile_type == profile_type)
        with self._engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [_model(BootstrapProfile, row) for row in rows]

    def disable_profile(self, profile_key: str) -> BootstrapProfile | None:
        self._ensure_schema()
        now = datetime.now(UTC)
        with self._engine.begin() as conn:
            conn.execute(
                update(aion_bootstrap_profiles)
                .where(aion_bootstrap_profiles.c.profile_key == profile_key)
                .values(status="disabled", disabled_at=now, updated_at=now)
            )
        return self.get_profile(profile_key)

    def save_bundle(self, bundle: SeedBundle) -> SeedBundle:
        self._ensure_schema()
        stored = _with_timestamps(bundle, created=True)
        with self._engine.begin() as conn:
            _upsert(
                conn,
                aion_seed_bundles,
                "seed_bundle_id",
                stored.seed_bundle_id,
                _values(aion_seed_bundles, stored),
            )
        return stored

    def get_bundle(self, seed_bundle_key: str) -> SeedBundle | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_seed_bundles).where(
                        aion_seed_bundles.c.seed_bundle_key == seed_bundle_key
                    )
                )
                .mappings()
                .first()
            )
        return _model_or_none(SeedBundle, row)

    def list_bundles(
        self,
        *,
        status: str | None = None,
        bundle_type: str | None = None,
        limit: int = 100,
    ) -> list[SeedBundle]:
        self._ensure_schema()
        query = (
            select(aion_seed_bundles).order_by(aion_seed_bundles.c.created_at.desc()).limit(limit)
        )
        if status is not None:
            query = query.where(aion_seed_bundles.c.status == status)
        if bundle_type is not None:
            query = query.where(aion_seed_bundles.c.bundle_type == bundle_type)
        with self._engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [_model(SeedBundle, row) for row in rows]

    def disable_bundle(self, seed_bundle_key: str) -> SeedBundle | None:
        self._ensure_schema()
        now = datetime.now(UTC)
        with self._engine.begin() as conn:
            conn.execute(
                update(aion_seed_bundles)
                .where(aion_seed_bundles.c.seed_bundle_key == seed_bundle_key)
                .values(status="disabled", disabled_at=now, updated_at=now)
            )
        return self.get_bundle(seed_bundle_key)

    def save_seed_execution(self, record: SeedExecutionRecord) -> SeedExecutionRecord:
        self._ensure_schema()
        stored = _with_timestamps(record, created=True, completed=True)
        with self._engine.begin() as conn:
            _upsert(
                conn,
                aion_seed_execution_records,
                "seed_execution_id",
                stored.seed_execution_id,
                _values(aion_seed_execution_records, stored),
            )
        return stored

    def get_seed_execution(self, seed_execution_id: str) -> SeedExecutionRecord | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_seed_execution_records).where(
                        aion_seed_execution_records.c.seed_execution_id == seed_execution_id
                    )
                )
                .mappings()
                .first()
            )
        return _model_or_none(SeedExecutionRecord, row)

    def list_seed_executions(
        self,
        *,
        status: str | None = None,
        seed_bundle_key: str | None = None,
        limit: int = 100,
    ) -> list[SeedExecutionRecord]:
        self._ensure_schema()
        query = (
            select(aion_seed_execution_records)
            .order_by(aion_seed_execution_records.c.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            query = query.where(aion_seed_execution_records.c.status == status)
        if seed_bundle_key is not None:
            query = query.where(aion_seed_execution_records.c.seed_bundle_key == seed_bundle_key)
        with self._engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [_model(SeedExecutionRecord, row) for row in rows]

    def save_finding(self, finding: SetupFinding) -> SetupFinding:
        self._ensure_schema()
        stored = _with_timestamps(finding, created=True)
        with self._engine.begin() as conn:
            _upsert(
                conn,
                aion_setup_findings,
                "setup_finding_id",
                stored.setup_finding_id,
                _values(aion_setup_findings, stored),
            )
        return stored

    def get_finding(self, setup_finding_id: str) -> SetupFinding | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_setup_findings).where(
                        aion_setup_findings.c.setup_finding_id == setup_finding_id
                    )
                )
                .mappings()
                .first()
            )
        return _model_or_none(SetupFinding, row)

    def list_findings(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> list[SetupFinding]:
        self._ensure_schema()
        query = (
            select(aion_setup_findings)
            .order_by(aion_setup_findings.c.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            query = query.where(aion_setup_findings.c.status == status)
        if severity is not None:
            query = query.where(aion_setup_findings.c.severity == severity)
        if category is not None:
            query = query.where(aion_setup_findings.c.category == category)
        with self._engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [_model(SetupFinding, row) for row in rows]

    def dismiss_finding(self, setup_finding_id: str, reason: str) -> SetupFinding | None:
        self._ensure_schema()
        now = datetime.now(UTC)
        with self._engine.begin() as conn:
            conn.execute(
                update(aion_setup_findings)
                .where(aion_setup_findings.c.setup_finding_id == setup_finding_id)
                .values(status="dismissed", dismissed_at=now, metadata={"dismiss_reason": reason})
            )
        return self.get_finding(setup_finding_id)

    def save_run(self, run: BootstrapRun) -> BootstrapRun:
        self._ensure_schema()
        stored = _with_timestamps(run, created=True, completed=True)
        payload = _run_values(stored)
        with self._engine.begin() as conn:
            _upsert(conn, aion_bootstrap_runs, "bootstrap_run_id", stored.bootstrap_run_id, payload)
        return stored

    def get_run(self, bootstrap_run_id: str) -> BootstrapRun | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_bootstrap_runs).where(
                        aion_bootstrap_runs.c.bootstrap_run_id == bootstrap_run_id
                    )
                )
                .mappings()
                .first()
            )
        return self._run_or_none(row)

    def list_runs(
        self,
        *,
        status: str | None = None,
        profile_key: str | None = None,
        limit: int = 50,
    ) -> list[BootstrapRun]:
        self._ensure_schema()
        query = (
            select(aion_bootstrap_runs)
            .order_by(aion_bootstrap_runs.c.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            query = query.where(aion_bootstrap_runs.c.status == status)
        if profile_key is not None:
            query = query.where(aion_bootstrap_runs.c.profile_key == profile_key)
        with self._engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [item for row in rows if (item := self._run_or_none(row)) is not None]

    def latest_run(self) -> BootstrapRun | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_bootstrap_runs)
                    .order_by(aion_bootstrap_runs.c.created_at.desc())
                    .limit(1)
                )
                .mappings()
                .first()
            )
        return self._run_or_none(row)

    def save_report(self, report: SetupReport) -> SetupReport:
        self._ensure_schema()
        stored = _with_timestamps(report, created=True)
        with self._engine.begin() as conn:
            _upsert(
                conn,
                aion_setup_reports,
                "setup_report_id",
                stored.setup_report_id,
                _values(aion_setup_reports, stored),
            )
        return stored

    def get_report(self, setup_report_id: str) -> SetupReport | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_setup_reports).where(
                        aion_setup_reports.c.setup_report_id == setup_report_id
                    )
                )
                .mappings()
                .first()
            )
        return _model_or_none(SetupReport, row)

    def list_reports(self, *, status: str | None = None, limit: int = 50) -> list[SetupReport]:
        self._ensure_schema()
        query = (
            select(aion_setup_reports).order_by(aion_setup_reports.c.created_at.desc()).limit(limit)
        )
        if status is not None:
            query = query.where(aion_setup_reports.c.status == status)
        with self._engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [_model(SetupReport, row) for row in rows]

    def latest_report(self) -> SetupReport | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_setup_reports)
                    .order_by(aion_setup_reports.c.created_at.desc())
                    .limit(1)
                )
                .mappings()
                .first()
            )
        return _model_or_none(SetupReport, row)

    def status(self, scope: list[str] | None = None) -> dict[str, Any]:
        latest = self.latest_report()
        latest_run = self.latest_run()
        return {
            "status": getattr(latest, "status", "not_run"),
            "local_ready": bool(getattr(latest, "local_ready", False)),
            "readiness_score": float(getattr(latest, "readiness_score", 0.0)),
            "latest_run_id": getattr(latest_run, "bootstrap_run_id", None),
            "latest_report_id": getattr(latest, "setup_report_id", None),
            "scope": scope or [],
        }

    def list_registry_records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for profile in self.list_profiles(limit=500):
            records.append(
                _registry_record(
                    "bootstrap_profile",
                    profile.bootstrap_profile_id,
                    profile.name,
                    profile.owner_scope,
                )
            )
        for bundle in self.list_bundles(limit=500):
            records.append(
                _registry_record(
                    "seed_bundle", bundle.seed_bundle_id, bundle.name, bundle.owner_scope
                )
            )
        for run in self.list_runs(limit=500):
            records.append(
                _registry_record("bootstrap_run", run.bootstrap_run_id, run.status, run.owner_scope)
            )
        for report in self.list_reports(limit=500):
            records.append(
                _registry_record(
                    "setup_report", report.setup_report_id, report.status, report.owner_scope
                )
            )
        return records

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        bootstrap_metadata.create_all(self._engine)
        self._schema_ready = True

    def _run_or_none(self, row: RowMapping | None) -> BootstrapRun | None:
        if row is None:
            return None
        profile = self.get_profile(str(row["profile_key"])) if row.get("profile_key") else None
        seed_executions: list[SeedExecutionRecord] = []
        for seed_id in row.get("seed_execution_ids", []):
            seed_execution = self.get_seed_execution(str(seed_id))
            if seed_execution is not None:
                seed_executions.append(seed_execution)
        findings: list[SetupFinding] = []
        for finding_id in row.get("setup_finding_ids", []):
            finding = self.get_finding(str(finding_id))
            if finding is not None:
                findings.append(finding)
        payload = dict(row)
        payload["bootstrap_profile"] = profile
        payload["seed_executions"] = seed_executions
        payload["setup_findings"] = findings
        payload.pop("bootstrap_profile_id", None)
        payload.pop("profile_key", None)
        payload.pop("seed_execution_ids", None)
        payload.pop("setup_finding_ids", None)
        return BootstrapRun.model_validate(payload)


def _model[TModel: BaseModel](model: type[TModel], row: RowMapping) -> TModel:
    return model.model_validate(dict(row))


def _model_or_none[TModel: BaseModel](model: type[TModel], row: RowMapping | None) -> TModel | None:
    if row is None:
        return None
    return _model(model, row)


def _with_timestamps[TModel: BaseModel](
    model: TModel, *, created: bool = False, completed: bool = False
) -> TModel:
    now = datetime.now(UTC)
    updates: dict[str, Any] = {}
    if created and getattr(model, "created_at", None) is None:
        updates["created_at"] = now
    if hasattr(model, "updated_at"):
        updates["updated_at"] = now
    if (
        completed
        and hasattr(model, "completed_at")
        and getattr(model, "completed_at", None) is None
    ):
        updates["completed_at"] = now
    if not updates:
        return model
    return model.model_copy(update=updates)


def _upsert(conn: Any, table: Table, id_column: str, id_value: str, values: dict[str, Any]) -> None:
    existing = conn.execute(
        select(table.c[id_column]).where(table.c[id_column] == id_value)
    ).first()
    if existing is None:
        conn.execute(insert(table).values(**values))
    else:
        conn.execute(update(table).where(table.c[id_column] == id_value).values(**values))


def _values(table: Table, model: BaseModel) -> dict[str, Any]:
    python_payload = model.model_dump(mode="python")
    json_payload = model.model_dump(mode="json")
    return {column.name: _column_value(column, python_payload, json_payload) for column in table.c}


def _run_values(run: BootstrapRun) -> dict[str, Any]:
    python_payload = run.model_dump(mode="python")
    json_payload = run.model_dump(mode="json")
    payload = {
        column.name: _column_value(column, python_payload, json_payload)
        for column in aion_bootstrap_runs.c
    }
    payload["bootstrap_profile_id"] = (
        run.bootstrap_profile.bootstrap_profile_id if run.bootstrap_profile is not None else None
    )
    payload["profile_key"] = (
        run.bootstrap_profile.profile_key if run.bootstrap_profile is not None else None
    )
    payload["seed_execution_ids"] = [item.seed_execution_id for item in run.seed_executions]
    payload["setup_finding_ids"] = [item.setup_finding_id for item in run.setup_findings]
    return payload


def _column_value(
    column: Any,
    python_payload: dict[str, Any],
    json_payload: dict[str, Any],
) -> Any:
    if isinstance(column.type, JSON):
        return json_payload.get(column.name)
    return python_payload.get(column.name)


def _registry_record(
    resource_type: str,
    resource_id: str,
    title: str,
    owner_scope: list[str],
) -> dict[str, Any]:
    return {
        "resource_uri": f"aion://{resource_type}/{resource_id}",
        "resource_type": resource_type,
        "resource_id": resource_id,
        "source_system": "bootstrap",
        "status": "active",
        "visibility": "operator",
        "sensitivity": "internal",
        "title": title,
        "summary": f"Bootstrap-owned {resource_type} record.",
        "owner_scope": owner_scope,
        "tags": ["bootstrap", "local_setup"],
        "refs": [],
        "metadata": {"source": "bootstrap"},
    }


__all__ = [
    "BootstrapRepository",
    "aion_bootstrap_profiles",
    "aion_bootstrap_runs",
    "aion_seed_bundles",
    "aion_seed_execution_records",
    "aion_setup_findings",
    "aion_setup_reports",
    "bootstrap_metadata",
]
