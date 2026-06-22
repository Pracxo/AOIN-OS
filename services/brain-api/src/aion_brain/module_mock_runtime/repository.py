"""Persistent repository for deterministic module mock runtime records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
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

from aion_brain.contracts.module_mock_runtime import (
    ModuleMockFinding,
    ModuleMockInvocationRequest,
    ModuleMockOutput,
    ModuleMockProfile,
    ModuleMockRun,
)

module_mock_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_module_mock_profiles = Table(
    "aion_module_mock_profiles",
    module_mock_metadata,
    Column("mock_profile_id", Text, primary_key=True),
    Column("profile_key", Text, nullable=False, unique=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("profile_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("supported_capability_types", json_payload_type, nullable=False),
    Column("supported_capability_keys", json_payload_type, nullable=False),
    Column("input_schema_hints", json_payload_type, nullable=False),
    Column("output_schema_hints", json_payload_type, nullable=False),
    Column("simulation_rules", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_module_mock_profiles_key", "profile_key"),
    Index("ix_aion_module_mock_profiles_status", "status"),
    Index("ix_aion_module_mock_profiles_type", "profile_type"),
    Index("ix_aion_module_mock_profiles_created", "created_at"),
)

aion_module_mock_invocation_requests = Table(
    "aion_module_mock_invocation_requests",
    module_mock_metadata,
    Column("mock_invocation_request_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("mock_profile_id", Text, nullable=True),
    Column("extension_package_id", Text, nullable=True),
    Column("module_slot_id", Text, nullable=True),
    Column("capability_binding_id", Text, nullable=False),
    Column("capability_key", Text, nullable=False),
    Column("invocation_type", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("input_payload_hash", Text, nullable=False),
    Column("redacted_input_payload", json_payload_type, nullable=False),
    Column("expected_output_shape", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("policy_refs", json_payload_type, nullable=False),
    Column("sandbox_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_module_mock_requests_trace", "trace_id"),
    Index("ix_aion_module_mock_requests_actor", "actor_id"),
    Index("ix_aion_module_mock_requests_workspace", "workspace_id"),
    Index("ix_aion_module_mock_requests_profile", "mock_profile_id"),
    Index("ix_aion_module_mock_requests_extension", "extension_package_id"),
    Index("ix_aion_module_mock_requests_slot", "module_slot_id"),
    Index("ix_aion_module_mock_requests_binding", "capability_binding_id"),
    Index("ix_aion_module_mock_requests_key", "capability_key"),
    Index("ix_aion_module_mock_requests_type", "invocation_type"),
    Index("ix_aion_module_mock_requests_mode", "mode"),
    Index("ix_aion_module_mock_requests_created", "created_at"),
)

aion_module_mock_runs = Table(
    "aion_module_mock_runs",
    module_mock_metadata,
    Column("module_mock_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("mock_invocation_request_id", Text, nullable=False),
    Column("mock_profile_id", Text, nullable=True),
    Column("extension_package_id", Text, nullable=True),
    Column("module_slot_id", Text, nullable=True),
    Column("capability_binding_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("checks_run", json_payload_type, nullable=False),
    Column("output_id", Text, nullable=True),
    Column("finding_ids", json_payload_type, nullable=False),
    Column("score", Float, nullable=False),
    Column("schema_valid", Boolean, nullable=False),
    Column("policy_valid", Boolean, nullable=False),
    Column("sandbox_valid", Boolean, nullable=False),
    Column("activation_allowed", Boolean, nullable=False),
    Column("execution_allowed", Boolean, nullable=False),
    Column("external_calls_made", Boolean, nullable=False),
    Column("code_loaded", Boolean, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_module_mock_runs_trace", "trace_id"),
    Index("ix_aion_module_mock_runs_request", "mock_invocation_request_id"),
    Index("ix_aion_module_mock_runs_profile", "mock_profile_id"),
    Index("ix_aion_module_mock_runs_slot", "module_slot_id"),
    Index("ix_aion_module_mock_runs_binding", "capability_binding_id"),
    Index("ix_aion_module_mock_runs_status", "status"),
    Index("ix_aion_module_mock_runs_mode", "mode"),
    Index("ix_aion_module_mock_runs_score", "score"),
    Index("ix_aion_module_mock_runs_schema", "schema_valid"),
    Index("ix_aion_module_mock_runs_activation", "activation_allowed"),
    Index("ix_aion_module_mock_runs_execution", "execution_allowed"),
    Index("ix_aion_module_mock_runs_external", "external_calls_made"),
    Index("ix_aion_module_mock_runs_code", "code_loaded"),
    Index("ix_aion_module_mock_runs_created", "created_at"),
)

aion_module_mock_outputs = Table(
    "aion_module_mock_outputs",
    module_mock_metadata,
    Column("module_mock_output_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("module_mock_run_id", Text, nullable=False),
    Column("capability_binding_id", Text, nullable=False),
    Column("capability_key", Text, nullable=False),
    Column("output_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("output_payload_hash", Text, nullable=False),
    Column("redacted_output_payload", json_payload_type, nullable=False),
    Column("output_summary", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_module_mock_outputs_trace", "trace_id"),
    Index("ix_aion_module_mock_outputs_run", "module_mock_run_id"),
    Index("ix_aion_module_mock_outputs_binding", "capability_binding_id"),
    Index("ix_aion_module_mock_outputs_key", "capability_key"),
    Index("ix_aion_module_mock_outputs_type", "output_type"),
    Index("ix_aion_module_mock_outputs_status", "status"),
    Index("ix_aion_module_mock_outputs_confidence", "confidence"),
    Index("ix_aion_module_mock_outputs_created", "created_at"),
)

aion_module_mock_findings = Table(
    "aion_module_mock_findings",
    module_mock_metadata,
    Column("module_mock_finding_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("module_mock_run_id", Text, nullable=True),
    Column("mock_invocation_request_id", Text, nullable=True),
    Column("module_slot_id", Text, nullable=True),
    Column("capability_binding_id", Text, nullable=True),
    Column("finding_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("recommended_action", Text, nullable=False),
    Column("refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Column("dismissed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_module_mock_findings_trace", "trace_id"),
    Index("ix_aion_module_mock_findings_run", "module_mock_run_id"),
    Index("ix_aion_module_mock_findings_request", "mock_invocation_request_id"),
    Index("ix_aion_module_mock_findings_slot", "module_slot_id"),
    Index("ix_aion_module_mock_findings_binding", "capability_binding_id"),
    Index("ix_aion_module_mock_findings_type", "finding_type"),
    Index("ix_aion_module_mock_findings_severity", "severity"),
    Index("ix_aion_module_mock_findings_status", "status"),
    Index("ix_aion_module_mock_findings_created", "created_at"),
)


class ModuleMockRuntimeRepository:
    """Store module mock runtime metadata without executing module code."""

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

    def save_profile(self, profile: ModuleMockProfile) -> ModuleMockProfile:
        now = _now()
        stored = profile.model_copy(
            update={"created_at": profile.created_at or now, "updated_at": now}
        )
        self._replace(
            aion_module_mock_profiles,
            "mock_profile_id",
            stored.mock_profile_id,
            _model_values(aion_module_mock_profiles, stored),
        )
        return stored

    def get_profile(self, mock_profile_id: str) -> ModuleMockProfile | None:
        return self._get(
            aion_module_mock_profiles,
            "mock_profile_id",
            mock_profile_id,
            ModuleMockProfile,
        )

    def get_profile_by_key(self, profile_key: str) -> ModuleMockProfile | None:
        return self._get(aion_module_mock_profiles, "profile_key", profile_key, ModuleMockProfile)

    def list_profiles(
        self,
        *,
        status: str | None = None,
        profile_type: str | None = None,
        limit: int = 100,
    ) -> list[ModuleMockProfile]:
        return self._list(
            aion_module_mock_profiles,
            ModuleMockProfile,
            {"status": status, "profile_type": profile_type},
            "created_at",
            limit,
        )

    def save_request(self, request: ModuleMockInvocationRequest) -> ModuleMockInvocationRequest:
        stored = request.model_copy(update={"created_at": request.created_at or _now()})
        self._replace(
            aion_module_mock_invocation_requests,
            "mock_invocation_request_id",
            stored.mock_invocation_request_id,
            _model_values(aion_module_mock_invocation_requests, stored),
        )
        return stored

    def get_request(self, mock_invocation_request_id: str) -> ModuleMockInvocationRequest | None:
        return self._get(
            aion_module_mock_invocation_requests,
            "mock_invocation_request_id",
            mock_invocation_request_id,
            ModuleMockInvocationRequest,
        )

    def list_requests(
        self,
        *,
        mock_profile_id: str | None = None,
        module_slot_id: str | None = None,
        capability_binding_id: str | None = None,
        mode: str | None = None,
        limit: int = 100,
    ) -> list[ModuleMockInvocationRequest]:
        return self._list(
            aion_module_mock_invocation_requests,
            ModuleMockInvocationRequest,
            {
                "mock_profile_id": mock_profile_id,
                "module_slot_id": module_slot_id,
                "capability_binding_id": capability_binding_id,
                "mode": mode,
            },
            "created_at",
            limit,
        )

    def save_output(self, output: ModuleMockOutput) -> ModuleMockOutput:
        stored = output.model_copy(update={"created_at": output.created_at or _now()})
        self._replace(
            aion_module_mock_outputs,
            "module_mock_output_id",
            stored.module_mock_output_id,
            _model_values(aion_module_mock_outputs, stored),
        )
        return stored

    def get_output(self, module_mock_output_id: str) -> ModuleMockOutput | None:
        return self._get(
            aion_module_mock_outputs,
            "module_mock_output_id",
            module_mock_output_id,
            ModuleMockOutput,
        )

    def list_outputs(
        self,
        *,
        module_mock_run_id: str | None = None,
        capability_binding_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ModuleMockOutput]:
        return self._list(
            aion_module_mock_outputs,
            ModuleMockOutput,
            {
                "module_mock_run_id": module_mock_run_id,
                "capability_binding_id": capability_binding_id,
                "status": status,
            },
            "created_at",
            limit,
        )

    def save_finding(self, finding: ModuleMockFinding) -> ModuleMockFinding:
        stored = finding.model_copy(update={"created_at": finding.created_at or _now()})
        self._replace(
            aion_module_mock_findings,
            "module_mock_finding_id",
            stored.module_mock_finding_id,
            _model_values(aion_module_mock_findings, stored),
        )
        return stored

    def get_finding(self, module_mock_finding_id: str) -> ModuleMockFinding | None:
        return self._get(
            aion_module_mock_findings,
            "module_mock_finding_id",
            module_mock_finding_id,
            ModuleMockFinding,
        )

    def list_findings(
        self,
        *,
        module_mock_run_id: str | None = None,
        capability_binding_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        finding_type: str | None = None,
        limit: int = 100,
    ) -> list[ModuleMockFinding]:
        return self._list(
            aion_module_mock_findings,
            ModuleMockFinding,
            {
                "module_mock_run_id": module_mock_run_id,
                "capability_binding_id": capability_binding_id,
                "status": status,
                "severity": severity,
                "finding_type": finding_type,
            },
            "created_at",
            limit,
        )

    def save_run(self, run: ModuleMockRun) -> ModuleMockRun:
        now = _now()
        stored = run.model_copy(
            update={"created_at": run.created_at or now, "completed_at": run.completed_at or now}
        )
        values = _model_values(aion_module_mock_runs, stored)
        values["output_id"] = stored.output.module_mock_output_id if stored.output else None
        values["finding_ids"] = [finding.module_mock_finding_id for finding in stored.findings]
        self._replace(
            aion_module_mock_runs,
            "module_mock_run_id",
            stored.module_mock_run_id,
            values,
        )
        return stored

    def get_run(self, module_mock_run_id: str) -> ModuleMockRun | None:
        base = self._get_row(aion_module_mock_runs, "module_mock_run_id", module_mock_run_id)
        if base is None:
            return None
        return self._row_to_run(base)

    def list_runs(
        self,
        *,
        module_slot_id: str | None = None,
        capability_binding_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ModuleMockRun]:
        rows = self._list_rows(
            aion_module_mock_runs,
            {
                "module_slot_id": module_slot_id,
                "capability_binding_id": capability_binding_id,
                "status": status,
            },
            "created_at",
            limit,
        )
        return [self._row_to_run(row) for row in rows]

    def status(self, scope: list[str] | None = None) -> dict[str, Any]:
        runs = self.list_runs(limit=1000)
        failed = [item for item in runs if item.status in {"failed", "blocked"}]
        return {
            "status": "warning" if failed else "healthy",
            "module_mock_run_count": len(runs),
            "failed_or_blocked_run_count": len(failed),
            "activation_allowed": False,
            "execution_allowed": False,
            "external_calls_made": False,
            "code_loaded": False,
            "scope": scope or [],
        }

    def list_registry_records(self, *, limit: int = 100) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        records.extend(
            _registry_record(
                "module_mock_profile",
                item.mock_profile_id,
                item.status,
                item.created_at,
            )
            for item in self.list_profiles(limit=limit)
        )
        records.extend(
            _registry_record(
                "module_mock_run",
                item.module_mock_run_id,
                item.status,
                item.created_at,
            )
            for item in self.list_runs(limit=limit)
        )
        records.extend(
            _registry_record(
                "module_mock_output", item.module_mock_output_id, item.status, item.created_at
            )
            for item in self.list_outputs(limit=limit)
        )
        records.extend(
            _registry_record(
                "module_mock_finding", item.module_mock_finding_id, item.status, item.created_at
            )
            for item in self.list_findings(limit=limit)
        )
        return records[:limit]

    def _replace(
        self,
        table: Table,
        key_column: str,
        key_value: str,
        values: dict[str, Any],
    ) -> None:
        self._ensure_schema()
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(table.c[key_column]).where(table.c[key_column] == key_value)
            ).first()
            if existing is None:
                connection.execute(insert(table).values(**values))
            else:
                statement = update(table).where(table.c[key_column] == key_value).values(**values)
                connection.execute(statement)

    def _get[T](self, table: Table, key_column: str, key_value: str, model: type[T]) -> T | None:
        row = self._get_row(table, key_column, key_value)
        return _row_to_model(row, model) if row is not None else None

    def _get_row(self, table: Table, key_column: str, key_value: str) -> RowMapping | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            return (
                connection.execute(select(table).where(table.c[key_column] == key_value))
                .mappings()
                .first()
            )

    def _list[T](
        self,
        table: Table,
        model: type[T],
        filters: dict[str, object | None],
        order_column: str,
        limit: int,
    ) -> list[T]:
        rows = self._list_rows(table, filters, order_column, limit)
        return [_row_to_model(row, model) for row in rows]

    def _list_rows(
        self,
        table: Table,
        filters: dict[str, object | None],
        order_column: str,
        limit: int,
    ) -> list[RowMapping]:
        self._ensure_schema()
        statement = select(table).order_by(getattr(table.c, order_column).desc()).limit(limit)
        for column, value in filters.items():
            if value is not None:
                statement = statement.where(getattr(table.c, column) == value)
        with self._engine.connect() as connection:
            return list(connection.execute(statement).mappings().all())

    def _row_to_run(self, row: RowMapping) -> ModuleMockRun:
        payload = dict(row)
        output_id = payload.pop("output_id", None)
        finding_ids = payload.pop("finding_ids", []) or []
        output = self.get_output(output_id) if output_id else None
        findings = [
            finding
            for finding_id in finding_ids
            if (finding := self.get_finding(str(finding_id))) is not None
        ]
        payload["output"] = output
        payload["findings"] = findings
        return ModuleMockRun.model_validate(payload)

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        module_mock_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        engine_kwargs: dict[str, Any] = {"connect_args": {"check_same_thread": False}}
        if database_url in {
            "sqlite://",
            "sqlite:///:memory:",
            "sqlite+pysqlite://",
            "sqlite+pysqlite:///:memory:",
        } or ":memory:" in database_url:
            engine_kwargs["poolclass"] = StaticPool
        return create_engine(database_url, **engine_kwargs)
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _model_values(table: Table, model: Any) -> dict[str, Any]:
    python_data = model.model_dump(mode="python")
    json_data = model.model_dump(mode="json")
    values: dict[str, Any] = {}
    for column in table.columns:
        if column.name not in python_data:
            continue
        value = python_data[column.name]
        values[column.name] = json_data[column.name] if isinstance(value, (dict, list)) else value
    return values


def _row_to_model[T](row: RowMapping, model: type[T]) -> T:
    fields = getattr(model, "model_fields", {})
    payload = {key: value for key, value in dict(row).items() if key in fields}
    return cast(T, model.model_validate(payload))  # type: ignore[attr-defined]


def _registry_record(
    resource_type: str, resource_id: str, status: str, created_at: datetime | None
) -> dict[str, Any]:
    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "status": status,
        "created_at": created_at.isoformat() if created_at else None,
    }


def _now() -> datetime:
    return datetime.now(UTC)


__all__ = ["ModuleMockRuntimeRepository", "module_mock_metadata"]
