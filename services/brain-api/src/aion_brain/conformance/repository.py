"""Persistent repository for conformance and readiness records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

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

from aion_brain.contracts.conformance import (
    CapabilityTestVector,
    ConformanceFinding,
    ConformanceProfile,
    ConformanceRun,
    MockInvocationRecord,
)
from aion_brain.contracts.readiness import ReadinessAssessment

conformance_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")


aion_conformance_profiles = Table(
    "aion_conformance_profiles",
    conformance_metadata,
    Column("conformance_profile_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("profile_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("required_checks", json_payload_type, nullable=False),
    Column("optional_checks", json_payload_type, nullable=False),
    Column("minimum_score", Float, nullable=False),
    Column("fail_on_critical", Boolean, nullable=False),
    Column("fail_on_missing_contract", Boolean, nullable=False),
    Column("fail_on_missing_policy_action", Boolean, nullable=False),
    Column("fail_on_missing_sandbox", Boolean, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_conformance_profiles_name", "name"),
    Index("ix_aion_conformance_profiles_status", "status"),
    Index("ix_aion_conformance_profiles_type", "profile_type"),
    Index("ix_aion_conformance_profiles_score", "minimum_score"),
    Index("ix_aion_conformance_profiles_created_at", "created_at"),
)

aion_capability_test_vectors = Table(
    "aion_capability_test_vectors",
    conformance_metadata,
    Column("test_vector_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("module_slot_id", Text, nullable=True),
    Column("capability_binding_id", Text, nullable=True),
    Column("extension_package_id", Text, nullable=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("vector_type", Text, nullable=False),
    Column("input_payload", json_payload_type, nullable=False),
    Column("expected_output_shape", json_payload_type, nullable=False),
    Column("expected_constraints", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_test_vectors_slot", "module_slot_id"),
    Index("ix_aion_test_vectors_binding", "capability_binding_id"),
    Index("ix_aion_test_vectors_extension", "extension_package_id"),
    Index("ix_aion_test_vectors_status", "status"),
    Index("ix_aion_test_vectors_type", "vector_type"),
    Index("ix_aion_test_vectors_created_at", "created_at"),
)

aion_mock_invocation_records = Table(
    "aion_mock_invocation_records",
    conformance_metadata,
    Column("mock_invocation_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("module_slot_id", Text, nullable=True),
    Column("capability_binding_id", Text, nullable=True),
    Column("extension_package_id", Text, nullable=True),
    Column("test_vector_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("invocation_type", Text, nullable=False),
    Column("input_payload_hash", Text, nullable=False),
    Column("redacted_input_payload", json_payload_type, nullable=False),
    Column("simulated_output", json_payload_type, nullable=False),
    Column("schema_valid", Boolean, nullable=False),
    Column("policy_valid", Boolean, nullable=False),
    Column("sandbox_valid", Boolean, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_mock_invocations_slot", "module_slot_id"),
    Index("ix_aion_mock_invocations_binding", "capability_binding_id"),
    Index("ix_aion_mock_invocations_extension", "extension_package_id"),
    Index("ix_aion_mock_invocations_vector", "test_vector_id"),
    Index("ix_aion_mock_invocations_status", "status"),
    Index("ix_aion_mock_invocations_type", "invocation_type"),
    Index("ix_aion_mock_invocations_schema", "schema_valid"),
    Index("ix_aion_mock_invocations_policy", "policy_valid"),
    Index("ix_aion_mock_invocations_sandbox", "sandbox_valid"),
    Index("ix_aion_mock_invocations_created_at", "created_at"),
)

aion_conformance_runs = Table(
    "aion_conformance_runs",
    conformance_metadata,
    Column("conformance_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("conformance_profile_id", Text, nullable=True),
    Column("module_slot_id", Text, nullable=True),
    Column("capability_binding_id", Text, nullable=True),
    Column("extension_package_id", Text, nullable=True),
    Column("checks_run", json_payload_type, nullable=False),
    Column("test_vector_ids", json_payload_type, nullable=False),
    Column("mock_invocations", json_payload_type, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("score", Float, nullable=False),
    Column("passed", Boolean, nullable=False),
    Column("blockers", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_conformance_runs_trace", "trace_id"),
    Index("ix_aion_conformance_runs_actor", "actor_id"),
    Index("ix_aion_conformance_runs_workspace", "workspace_id"),
    Index("ix_aion_conformance_runs_status", "status"),
    Index("ix_aion_conformance_runs_mode", "mode"),
    Index("ix_aion_conformance_runs_profile", "conformance_profile_id"),
    Index("ix_aion_conformance_runs_slot", "module_slot_id"),
    Index("ix_aion_conformance_runs_binding", "capability_binding_id"),
    Index("ix_aion_conformance_runs_extension", "extension_package_id"),
    Index("ix_aion_conformance_runs_score", "score"),
    Index("ix_aion_conformance_runs_passed", "passed"),
    Index("ix_aion_conformance_runs_created_at", "created_at"),
)

aion_conformance_findings = Table(
    "aion_conformance_findings",
    conformance_metadata,
    Column("conformance_finding_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("conformance_run_id", Text, nullable=True),
    Column("module_slot_id", Text, nullable=True),
    Column("capability_binding_id", Text, nullable=True),
    Column("extension_package_id", Text, nullable=True),
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
    Index("ix_aion_conformance_findings_run", "conformance_run_id"),
    Index("ix_aion_conformance_findings_slot", "module_slot_id"),
    Index("ix_aion_conformance_findings_binding", "capability_binding_id"),
    Index("ix_aion_conformance_findings_extension", "extension_package_id"),
    Index("ix_aion_conformance_findings_type", "finding_type"),
    Index("ix_aion_conformance_findings_severity", "severity"),
    Index("ix_aion_conformance_findings_status", "status"),
    Index("ix_aion_conformance_findings_created_at", "created_at"),
)

aion_extension_readiness_assessments = Table(
    "aion_extension_readiness_assessments",
    conformance_metadata,
    Column("readiness_assessment_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("extension_package_id", Text, nullable=True),
    Column("module_slot_id", Text, nullable=True),
    Column("capability_binding_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("readiness_level", Text, nullable=False),
    Column("activation_ready", Boolean, nullable=False),
    Column("minimum_score", Float, nullable=False),
    Column("actual_score", Float, nullable=False),
    Column("conformance_run_ids", json_payload_type, nullable=False),
    Column("compatibility_run_ids", json_payload_type, nullable=False),
    Column("validation_run_ids", json_payload_type, nullable=False),
    Column("blocker_refs", json_payload_type, nullable=False),
    Column("warning_refs", json_payload_type, nullable=False),
    Column("recommendations", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_readiness_trace", "trace_id"),
    Index("ix_aion_readiness_actor", "actor_id"),
    Index("ix_aion_readiness_workspace", "workspace_id"),
    Index("ix_aion_readiness_extension", "extension_package_id"),
    Index("ix_aion_readiness_slot", "module_slot_id"),
    Index("ix_aion_readiness_binding", "capability_binding_id"),
    Index("ix_aion_readiness_status", "status"),
    Index("ix_aion_readiness_level", "readiness_level"),
    Index("ix_aion_readiness_activation", "activation_ready"),
    Index("ix_aion_readiness_score", "actual_score"),
    Index("ix_aion_readiness_created_at", "created_at"),
)


class ConformanceRepository:
    """Store conformance records without activating modules."""

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

    def save_profile(self, profile: ConformanceProfile) -> ConformanceProfile:
        now = datetime.now(UTC)
        stored = profile.model_copy(
            update={"created_at": profile.created_at or now, "updated_at": now}
        )
        self._replace(
            aion_conformance_profiles,
            "conformance_profile_id",
            stored.conformance_profile_id,
            _model_values(aion_conformance_profiles, stored),
        )
        return stored

    def get_profile(self, conformance_profile_id: str) -> ConformanceProfile | None:
        return self._get(
            aion_conformance_profiles,
            "conformance_profile_id",
            conformance_profile_id,
            ConformanceProfile,
        )

    def list_profiles(
        self,
        *,
        status: str | None = None,
        profile_type: str | None = None,
        include_disabled: bool = False,
        limit: int = 100,
    ) -> list[ConformanceProfile]:
        items = self._list(
            aion_conformance_profiles,
            ConformanceProfile,
            {"status": status, "profile_type": profile_type},
            "created_at",
            limit,
        )
        return items if include_disabled else [item for item in items if item.status != "disabled"]

    def save_vector(self, vector: CapabilityTestVector) -> CapabilityTestVector:
        now = datetime.now(UTC)
        stored = vector.model_copy(
            update={"created_at": vector.created_at or now, "updated_at": now}
        )
        self._replace(
            aion_capability_test_vectors,
            "test_vector_id",
            stored.test_vector_id,
            _model_values(aion_capability_test_vectors, stored),
        )
        return stored

    def get_vector(self, test_vector_id: str) -> CapabilityTestVector | None:
        return self._get(
            aion_capability_test_vectors, "test_vector_id", test_vector_id, CapabilityTestVector
        )

    def list_vectors(
        self,
        *,
        module_slot_id: str | None = None,
        capability_binding_id: str | None = None,
        extension_package_id: str | None = None,
        status: str | None = None,
        vector_type: str | None = None,
        include_disabled: bool = False,
        limit: int = 100,
    ) -> list[CapabilityTestVector]:
        items = self._list(
            aion_capability_test_vectors,
            CapabilityTestVector,
            {
                "module_slot_id": module_slot_id,
                "capability_binding_id": capability_binding_id,
                "extension_package_id": extension_package_id,
                "status": status,
                "vector_type": vector_type,
            },
            "created_at",
            limit,
        )
        return items if include_disabled else [item for item in items if item.status != "disabled"]

    def save_mock_invocation(self, record: MockInvocationRecord) -> MockInvocationRecord:
        stored = record.model_copy(update={"created_at": record.created_at or datetime.now(UTC)})
        self._replace(
            aion_mock_invocation_records,
            "mock_invocation_id",
            stored.mock_invocation_id,
            _model_values(aion_mock_invocation_records, stored),
        )
        return stored

    def list_mock_invocations(
        self,
        *,
        capability_binding_id: str | None = None,
        test_vector_id: str | None = None,
        limit: int = 100,
    ) -> list[MockInvocationRecord]:
        return self._list(
            aion_mock_invocation_records,
            MockInvocationRecord,
            {"capability_binding_id": capability_binding_id, "test_vector_id": test_vector_id},
            "created_at",
            limit,
        )

    def save_run(self, run: ConformanceRun) -> ConformanceRun:
        stored = run.model_copy(
            update={
                "created_at": run.created_at or datetime.now(UTC),
                "completed_at": run.completed_at or datetime.now(UTC),
            }
        )
        self._replace(
            aion_conformance_runs,
            "conformance_run_id",
            stored.conformance_run_id,
            _model_values(aion_conformance_runs, stored),
        )
        return stored

    def get_run(self, conformance_run_id: str) -> ConformanceRun | None:
        return self._get(
            aion_conformance_runs, "conformance_run_id", conformance_run_id, ConformanceRun
        )

    def list_runs(
        self,
        *,
        status: str | None = None,
        module_slot_id: str | None = None,
        capability_binding_id: str | None = None,
        extension_package_id: str | None = None,
        limit: int = 100,
    ) -> list[ConformanceRun]:
        return self._list(
            aion_conformance_runs,
            ConformanceRun,
            {
                "status": status,
                "module_slot_id": module_slot_id,
                "capability_binding_id": capability_binding_id,
                "extension_package_id": extension_package_id,
            },
            "created_at",
            limit,
        )

    def save_finding(self, finding: ConformanceFinding) -> ConformanceFinding:
        stored = finding.model_copy(update={"created_at": finding.created_at or datetime.now(UTC)})
        self._replace(
            aion_conformance_findings,
            "conformance_finding_id",
            stored.conformance_finding_id,
            _model_values(aion_conformance_findings, stored),
        )
        return stored

    def get_finding(self, conformance_finding_id: str) -> ConformanceFinding | None:
        return self._get(
            aion_conformance_findings,
            "conformance_finding_id",
            conformance_finding_id,
            ConformanceFinding,
        )

    def list_findings(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        finding_type: str | None = None,
        module_slot_id: str | None = None,
        capability_binding_id: str | None = None,
        extension_package_id: str | None = None,
        limit: int = 100,
    ) -> list[ConformanceFinding]:
        return self._list(
            aion_conformance_findings,
            ConformanceFinding,
            {
                "status": status,
                "severity": severity,
                "finding_type": finding_type,
                "module_slot_id": module_slot_id,
                "capability_binding_id": capability_binding_id,
                "extension_package_id": extension_package_id,
            },
            "created_at",
            limit,
        )

    def save_readiness(self, assessment: ReadinessAssessment) -> ReadinessAssessment:
        stored = assessment.model_copy(
            update={
                "created_at": assessment.created_at or datetime.now(UTC),
                "completed_at": assessment.completed_at or datetime.now(UTC),
            }
        )
        self._replace(
            aion_extension_readiness_assessments,
            "readiness_assessment_id",
            stored.readiness_assessment_id,
            _model_values(aion_extension_readiness_assessments, stored),
        )
        return stored

    def get_readiness(self, readiness_assessment_id: str) -> ReadinessAssessment | None:
        return self._get(
            aion_extension_readiness_assessments,
            "readiness_assessment_id",
            readiness_assessment_id,
            ReadinessAssessment,
        )

    def list_readiness(
        self,
        *,
        status: str | None = None,
        readiness_level: str | None = None,
        module_slot_id: str | None = None,
        capability_binding_id: str | None = None,
        extension_package_id: str | None = None,
        limit: int = 100,
    ) -> list[ReadinessAssessment]:
        return self._list(
            aion_extension_readiness_assessments,
            ReadinessAssessment,
            {
                "status": status,
                "readiness_level": readiness_level,
                "module_slot_id": module_slot_id,
                "capability_binding_id": capability_binding_id,
                "extension_package_id": extension_package_id,
            },
            "created_at",
            limit,
        )

    def status(self, scope: list[str] | None = None) -> dict[str, Any]:
        runs = self.list_runs(limit=1000)
        findings = self.list_findings(status="open", limit=1000)
        readiness = self.list_readiness(limit=1000)
        failed = [run for run in runs if run.status in {"failed", "blocked"}]
        blocked = [item for item in readiness if item.status == "blocked"]
        return {
            "status": "blocked" if blocked or failed else "warning" if findings else "healthy",
            "conformance_run_count": len(runs),
            "failed_conformance_count": len(failed),
            "open_finding_count": len(findings),
            "blocked_readiness_count": len(blocked),
            "scope": scope or [],
        }

    def list_registry_records(self, *, limit: int = 100) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        records.extend(
            _registry_record(
                "conformance_profile", item.conformance_profile_id, item.status, item.created_at
            )
            for item in self.list_profiles(include_disabled=True, limit=limit)
        )
        records.extend(
            _registry_record(
                "capability_test_vector", item.test_vector_id, item.status, item.created_at
            )
            for item in self.list_vectors(include_disabled=True, limit=limit)
        )
        records.extend(
            _registry_record(
                "conformance_run", item.conformance_run_id, item.status, item.created_at
            )
            for item in self.list_runs(limit=limit)
        )
        records.extend(
            _registry_record(
                "conformance_finding", item.conformance_finding_id, item.status, item.created_at
            )
            for item in self.list_findings(limit=limit)
        )
        records.extend(
            _registry_record(
                "readiness_assessment", item.readiness_assessment_id, item.status, item.created_at
            )
            for item in self.list_readiness(limit=limit)
        )
        return records[:limit]

    def _replace(
        self, table: Table, key_column: str, key_value: str, values: dict[str, Any]
    ) -> None:
        self._ensure_schema()
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(table.c[key_column]).where(table.c[key_column] == key_value)
            ).first()
            if existing is None:
                connection.execute(insert(table).values(**values))
            else:
                connection.execute(
                    update(table).where(table.c[key_column] == key_value).values(**values)
                )

    def _get[T](self, table: Table, key_column: str, key_value: str, model: type[T]) -> T | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(table).where(table.c[key_column] == key_value))
                .mappings()
                .first()
            )
        return _row_to_model(row, model) if row is not None else None

    def _list[T](
        self,
        table: Table,
        model: type[T],
        filters: dict[str, object | None],
        order_column: str,
        limit: int,
    ) -> list[T]:
        self._ensure_schema()
        statement = select(table).order_by(getattr(table.c, order_column).desc()).limit(limit)
        for column, value in filters.items():
            if value is not None:
                statement = statement.where(getattr(table.c, column) == value)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_model(row, model) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        conformance_metadata.create_all(self._engine)
        self._schema_ready = True


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
    return model(**{key: value for key, value in dict(row).items() if key in fields})


def _registry_record(
    resource_type: str,
    resource_id: str,
    status: str,
    created_at: datetime | None,
) -> dict[str, Any]:
    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "status": "active" if status not in {"archived", "disabled"} else status,
        "created_at": created_at,
        "metadata": {"conformance_status": status, "source_records_mutated": False},
    }


__all__ = [
    "ConformanceRepository",
    "aion_capability_test_vectors",
    "aion_conformance_findings",
    "aion_conformance_profiles",
    "aion_conformance_runs",
    "aion_extension_readiness_assessments",
    "aion_mock_invocation_records",
    "conformance_metadata",
]
