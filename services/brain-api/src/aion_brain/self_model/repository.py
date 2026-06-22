"""Persistence for AION self-model records."""

from __future__ import annotations

from typing import Any

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
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.capability_awareness import CapabilityAwarenessRecord
from aion_brain.contracts.confidence import (
    ConfidenceCalibration,
    IntrospectionSnapshot,
    SelfAssessmentRun,
)
from aion_brain.contracts.self_model import LimitationRecord, SelfModelProfile

self_model_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_self_model_profiles = Table(
    "aion_self_model_profiles",
    self_model_metadata,
    Column("self_model_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("full_name", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("operating_principles", json_payload_type, nullable=False),
    Column("architecture_refs", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_self_model_profiles_name", "name"),
    Index("ix_aion_self_model_profiles_version", "version"),
    Index("ix_aion_self_model_profiles_status", "status"),
    Index("ix_aion_self_model_profiles_created_at", "created_at"),
)

aion_capability_awareness_records = Table(
    "aion_capability_awareness_records",
    self_model_metadata,
    Column("awareness_id", Text, primary_key=True),
    Column("capability_key", Text, nullable=False),
    Column("capability_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("availability", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("requires_policy", Boolean, nullable=False),
    Column("requires_approval", Boolean, nullable=False),
    Column("requires_autonomy", Boolean, nullable=False),
    Column("dry_run_only", Boolean, nullable=False),
    Column("source_refs", json_payload_type, nullable=False),
    Column("limitations", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("checked_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_capability_awareness_records_capability_key", "capability_key"),
    Index("ix_aion_capability_awareness_records_capability_type", "capability_type"),
    Index("ix_aion_capability_awareness_records_status", "status"),
    Index("ix_aion_capability_awareness_records_availability", "availability"),
    Index("ix_aion_capability_awareness_records_mode", "mode"),
    Index("ix_aion_capability_awareness_records_risk_level", "risk_level"),
    Index("ix_aion_capability_awareness_records_dry_run_only", "dry_run_only"),
    Index("ix_aion_capability_awareness_records_checked_at", "checked_at"),
)

aion_limitation_records = Table(
    "aion_limitation_records",
    self_model_metadata,
    Column("limitation_id", Text, primary_key=True),
    Column("limitation_key", Text, nullable=False, unique=True),
    Column("category", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("affected_capabilities", json_payload_type, nullable=False),
    Column("workaround", Text, nullable=True),
    Column("disclosure_required", Boolean, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_limitation_records_limitation_key", "limitation_key"),
    Index("ix_aion_limitation_records_category", "category"),
    Index("ix_aion_limitation_records_status", "status"),
    Index("ix_aion_limitation_records_severity", "severity"),
    Index("ix_aion_limitation_records_disclosure_required", "disclosure_required"),
    Index("ix_aion_limitation_records_created_at", "created_at"),
)

aion_confidence_calibration_records = Table(
    "aion_confidence_calibration_records",
    self_model_metadata,
    Column("calibration_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("response_id", Text, nullable=True),
    Column("reasoning_id", Text, nullable=True),
    Column("decision_frame_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=True),
    Column("confidence", Float, nullable=False),
    Column("confidence_level", Text, nullable=False),
    Column("grounding_status", Text, nullable=False),
    Column("uncertainty_factors", json_payload_type, nullable=False),
    Column("required_disclosures", json_payload_type, nullable=False),
    Column("clarification_recommended", Boolean, nullable=False),
    Column("verification_recommended", Boolean, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_confidence_calibration_records_trace_id", "trace_id"),
    Index("ix_aion_confidence_calibration_records_response_id", "response_id"),
    Index("ix_aion_confidence_calibration_records_reasoning_id", "reasoning_id"),
    Index("ix_aion_confidence_calibration_records_decision_frame_id", "decision_frame_id"),
    Index("ix_aion_confidence_calibration_records_source_type", "source_type"),
    Index("ix_aion_confidence_calibration_records_source_id", "source_id"),
    Index("ix_aion_confidence_calibration_records_confidence", "confidence"),
    Index("ix_aion_confidence_calibration_records_confidence_level", "confidence_level"),
    Index("ix_aion_confidence_calibration_records_grounding_status", "grounding_status"),
    Index(
        "ix_aion_confidence_calibration_records_clarification_recommended",
        "clarification_recommended",
    ),
    Index(
        "ix_aion_confidence_calibration_records_verification_recommended",
        "verification_recommended",
    ),
    Index("ix_aion_confidence_calibration_records_created_at", "created_at"),
)

aion_self_assessment_runs = Table(
    "aion_self_assessment_runs",
    self_model_metadata,
    Column("self_assessment_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("assessment_type", Text, nullable=False),
    Column("capability_count", Integer, nullable=False),
    Column("active_capability_count", Integer, nullable=False),
    Column("disabled_capability_count", Integer, nullable=False),
    Column("unavailable_capability_count", Integer, nullable=False),
    Column("limitation_count", Integer, nullable=False),
    Column("critical_limitation_count", Integer, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("recommendations", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_self_assessment_runs_trace_id", "trace_id"),
    Index("ix_aion_self_assessment_runs_status", "status"),
    Index("ix_aion_self_assessment_runs_assessment_type", "assessment_type"),
    Index("ix_aion_self_assessment_runs_created_at", "created_at"),
)

aion_introspection_snapshots = Table(
    "aion_introspection_snapshots",
    self_model_metadata,
    Column("introspection_snapshot_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("snapshot_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("self_model", json_payload_type, nullable=False),
    Column("capability_inventory", json_payload_type, nullable=False),
    Column("limitations", json_payload_type, nullable=False),
    Column("calibration_summary", json_payload_type, nullable=False),
    Column("operator_summary", json_payload_type, nullable=False),
    Column("config_summary", json_payload_type, nullable=False),
    Column("audit_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_introspection_snapshots_trace_id", "trace_id"),
    Index("ix_aion_introspection_snapshots_actor_id", "actor_id"),
    Index("ix_aion_introspection_snapshots_workspace_id", "workspace_id"),
    Index("ix_aion_introspection_snapshots_snapshot_type", "snapshot_type"),
    Index("ix_aion_introspection_snapshots_status", "status"),
    Index("ix_aion_introspection_snapshots_created_at", "created_at"),
)


class SelfModelRepository:
    """Repository for self-model, capability, limitation, and calibration records."""

    def __init__(
        self,
        database_url: str | None = None,
        *,
        engine: Engine | None = None,
        auto_create: bool = True,
    ) -> None:
        url = database_url or "sqlite+pysqlite:///:memory:"
        self._engine = engine or create_engine(
            url,
            connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
            poolclass=StaticPool if url.startswith("sqlite") else QueuePool,
            pool_pre_ping=not url.startswith("sqlite"),
        )
        self._auto_create = auto_create
        self._schema_ready = False

    def save_profile(self, profile: SelfModelProfile) -> SelfModelProfile:
        self._upsert(aion_self_model_profiles, "self_model_id", profile.model_dump(mode="python"))
        return profile

    def get_active_profile(self) -> SelfModelProfile | None:
        row = self._first(
            select(aion_self_model_profiles)
            .where(aion_self_model_profiles.c.status == "active")
            .order_by(aion_self_model_profiles.c.updated_at.desc())
        )
        return SelfModelProfile(**dict(row)) if row is not None else None

    def save_capability_awareness(
        self, record: CapabilityAwarenessRecord
    ) -> CapabilityAwarenessRecord:
        self._upsert(
            aion_capability_awareness_records, "awareness_id", record.model_dump(mode="python")
        )
        return record

    def list_capability_awareness(
        self,
        *,
        status: str | None = None,
        capability_type: str | None = None,
        limit: int = 500,
    ) -> list[CapabilityAwarenessRecord]:
        statement = select(aion_capability_awareness_records).order_by(
            aion_capability_awareness_records.c.checked_at.desc()
        )
        if status:
            statement = statement.where(aion_capability_awareness_records.c.status == status)
        if capability_type:
            statement = statement.where(
                aion_capability_awareness_records.c.capability_type == capability_type
            )
        return [CapabilityAwarenessRecord(**dict(row)) for row in self._all(statement.limit(limit))]

    def get_capability_awareness(self, capability_key: str) -> CapabilityAwarenessRecord | None:
        row = self._first(
            select(aion_capability_awareness_records)
            .where(aion_capability_awareness_records.c.capability_key == capability_key)
            .order_by(aion_capability_awareness_records.c.checked_at.desc())
        )
        return CapabilityAwarenessRecord(**dict(row)) if row is not None else None

    def save_limitation(self, limitation: LimitationRecord) -> LimitationRecord:
        self._upsert(aion_limitation_records, "limitation_id", limitation.model_dump(mode="python"))
        return limitation

    def get_limitation(self, limitation_id: str) -> LimitationRecord | None:
        row = self._first(
            select(aion_limitation_records).where(
                aion_limitation_records.c.limitation_id == limitation_id
            )
        )
        return LimitationRecord(**dict(row)) if row is not None else None

    def get_limitation_by_key(self, limitation_key: str) -> LimitationRecord | None:
        row = self._first(
            select(aion_limitation_records).where(
                aion_limitation_records.c.limitation_key == limitation_key
            )
        )
        return LimitationRecord(**dict(row)) if row is not None else None

    def list_limitations(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        category: str | None = None,
        severity: str | None = None,
        disclosure_required: bool | None = None,
        limit: int = 500,
    ) -> list[LimitationRecord]:
        statement = select(aion_limitation_records).order_by(
            aion_limitation_records.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_limitation_records.c.status == status)
        if category:
            statement = statement.where(aion_limitation_records.c.category == category)
        if severity:
            statement = statement.where(aion_limitation_records.c.severity == severity)
        if disclosure_required is not None:
            statement = statement.where(
                aion_limitation_records.c.disclosure_required == disclosure_required
            )
        return _filter_scope(
            [LimitationRecord(**dict(row)) for row in self._all(statement)], scope, limit
        )

    def save_confidence_calibration(
        self, calibration: ConfidenceCalibration
    ) -> ConfidenceCalibration:
        self._upsert(
            aion_confidence_calibration_records,
            "calibration_id",
            calibration.model_dump(mode="python"),
        )
        return calibration

    def list_confidence_calibrations(
        self,
        *,
        trace_id: str | None = None,
        response_id: str | None = None,
        limit: int = 100,
    ) -> list[ConfidenceCalibration]:
        statement = select(aion_confidence_calibration_records).order_by(
            aion_confidence_calibration_records.c.created_at.desc()
        )
        if trace_id:
            statement = statement.where(aion_confidence_calibration_records.c.trace_id == trace_id)
        if response_id:
            statement = statement.where(
                aion_confidence_calibration_records.c.response_id == response_id
            )
        return [ConfidenceCalibration(**dict(row)) for row in self._all(statement.limit(limit))]

    def save_assessment_run(self, run: SelfAssessmentRun) -> SelfAssessmentRun:
        self._upsert(aion_self_assessment_runs, "self_assessment_id", run.model_dump(mode="python"))
        return run

    def get_assessment_run(self, self_assessment_id: str) -> SelfAssessmentRun | None:
        row = self._first(
            select(aion_self_assessment_runs).where(
                aion_self_assessment_runs.c.self_assessment_id == self_assessment_id
            )
        )
        return SelfAssessmentRun(**dict(row)) if row is not None else None

    def list_assessment_runs(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[SelfAssessmentRun]:
        statement = select(aion_self_assessment_runs).order_by(
            aion_self_assessment_runs.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_self_assessment_runs.c.status == status)
        return _filter_scope(
            [SelfAssessmentRun(**dict(row)) for row in self._all(statement)], scope, limit
        )

    def save_introspection_snapshot(self, snapshot: IntrospectionSnapshot) -> IntrospectionSnapshot:
        values = snapshot.model_dump(mode="python")
        json_values = snapshot.model_dump(mode="json")
        for field in (
            "self_model",
            "capability_inventory",
            "limitations",
            "calibration_summary",
            "operator_summary",
            "config_summary",
            "audit_refs",
            "metadata",
        ):
            values[field] = json_values[field]
        self._upsert(
            aion_introspection_snapshots,
            "introspection_snapshot_id",
            values,
        )
        return snapshot

    def get_introspection_snapshot(
        self, introspection_snapshot_id: str
    ) -> IntrospectionSnapshot | None:
        row = self._first(
            select(aion_introspection_snapshots).where(
                aion_introspection_snapshots.c.introspection_snapshot_id
                == introspection_snapshot_id
            )
        )
        return IntrospectionSnapshot(**dict(row)) if row is not None else None

    def list_introspection_snapshots(
        self,
        scope: list[str],
        *,
        snapshot_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[IntrospectionSnapshot]:
        statement = select(aion_introspection_snapshots).order_by(
            aion_introspection_snapshots.c.created_at.desc()
        )
        if snapshot_type:
            statement = statement.where(
                aion_introspection_snapshots.c.snapshot_type == snapshot_type
            )
        if status:
            statement = statement.where(aion_introspection_snapshots.c.status == status)
        return _filter_scope(
            [IntrospectionSnapshot(**dict(row)) for row in self._all(statement)], scope, limit
        )

    def _upsert(self, table: Table, key: str, values: dict[str, Any]) -> None:
        self._ensure_schema()
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(table.c[key]).where(table.c[key] == values[key])
            ).first()
            if existing is None:
                connection.execute(insert(table).values(**values))
            else:
                connection.execute(
                    update(table).where(table.c[key] == values[key]).values(**values)
                )

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        if self._auto_create:
            self_model_metadata.create_all(self._engine)
        self._schema_ready = True

    def _first(self, statement: Any) -> RowMapping | None:
        self._ensure_schema()
        with self._engine.begin() as connection:
            return connection.execute(statement).mappings().first()

    def _all(self, statement: Any) -> list[RowMapping]:
        self._ensure_schema()
        with self._engine.begin() as connection:
            return list(connection.execute(statement).mappings().all())


def _filter_scope(items: list[Any], scope: list[str], limit: int) -> list[Any]:
    filtered: list[Any] = []
    for item in items:
        owner_scope = getattr(item, "owner_scope", [])
        if bool(set(owner_scope).intersection(set(scope))):
            filtered.append(item)
        if len(filtered) >= limit:
            break
    return filtered
