"""Persistence for audit integrity and provenance records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
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
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.audit_integrity import (
    AuditEntry,
    AuditExportRecord,
    AuditIntegrityCheckpoint,
    AuditVerificationRun,
    ProvenanceLink,
)

audit_integrity_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_audit_entries = Table(
    "aion_audit_entries",
    audit_integrity_metadata,
    Column("audit_entry_id", Text, primary_key=True),
    Column("sequence_number", BigInteger, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("correlation_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("action_type", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("resource_id", Text, nullable=True),
    Column("event_type", Text, nullable=False),
    Column("outcome", Text, nullable=False),
    Column("risk_level", Text, nullable=True),
    Column("policy_decision_id", Text, nullable=True),
    Column("autonomy_decision_id", Text, nullable=True),
    Column("risk_assessment_id", Text, nullable=True),
    Column("approval_request_id", Text, nullable=True),
    Column("command_id", Text, nullable=True),
    Column("source_component", Text, nullable=False),
    Column("payload_hash", Text, nullable=False),
    Column("previous_hash", Text, nullable=True),
    Column("entry_hash", Text, nullable=False),
    Column("hash_algorithm", Text, nullable=False),
    Column("canonical_payload", json_payload_type, nullable=False),
    Column("redaction_metadata", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("sequence_number", name="uq_aion_audit_entries_sequence"),
    UniqueConstraint("entry_hash", name="uq_aion_audit_entries_entry_hash"),
    Index("ix_aion_audit_entries_sequence_number", "sequence_number"),
    Index("ix_aion_audit_entries_trace_id", "trace_id"),
    Index("ix_aion_audit_entries_correlation_id", "correlation_id"),
    Index("ix_aion_audit_entries_actor_id", "actor_id"),
    Index("ix_aion_audit_entries_workspace_id", "workspace_id"),
    Index("ix_aion_audit_entries_action_type", "action_type"),
    Index("ix_aion_audit_entries_resource_type", "resource_type"),
    Index("ix_aion_audit_entries_resource_id", "resource_id"),
    Index("ix_aion_audit_entries_event_type", "event_type"),
    Index("ix_aion_audit_entries_outcome", "outcome"),
    Index("ix_aion_audit_entries_source_component", "source_component"),
    Index("ix_aion_audit_entries_entry_hash", "entry_hash"),
    Index("ix_aion_audit_entries_previous_hash", "previous_hash"),
    Index("ix_aion_audit_entries_created_at", "created_at"),
)

aion_audit_integrity_checkpoints = Table(
    "aion_audit_integrity_checkpoints",
    audit_integrity_metadata,
    Column("checkpoint_id", Text, primary_key=True),
    Column("from_sequence", BigInteger, nullable=False),
    Column("to_sequence", BigInteger, nullable=False),
    Column("entry_count", Integer, nullable=False),
    Column("root_hash", Text, nullable=False),
    Column("previous_checkpoint_hash", Text, nullable=True),
    Column("checkpoint_hash", Text, nullable=False),
    Column("hash_algorithm", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_audit_checkpoints_from_sequence", "from_sequence"),
    Index("ix_aion_audit_checkpoints_to_sequence", "to_sequence"),
    Index("ix_aion_audit_checkpoints_root_hash", "root_hash"),
    Index("ix_aion_audit_checkpoints_checkpoint_hash", "checkpoint_hash"),
    Index("ix_aion_audit_checkpoints_status", "status"),
    Index("ix_aion_audit_checkpoints_created_at", "created_at"),
)

aion_provenance_links = Table(
    "aion_provenance_links",
    audit_integrity_metadata,
    Column("provenance_link_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column("relation_type", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("audit_entry_id", Text, nullable=True),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_provenance_links_trace_id", "trace_id"),
    Index("ix_aion_provenance_links_source_type", "source_type"),
    Index("ix_aion_provenance_links_source_id", "source_id"),
    Index("ix_aion_provenance_links_target_type", "target_type"),
    Index("ix_aion_provenance_links_target_id", "target_id"),
    Index("ix_aion_provenance_links_relation_type", "relation_type"),
    Index("ix_aion_provenance_links_audit_entry_id", "audit_entry_id"),
    Index("ix_aion_provenance_links_deleted_at", "deleted_at"),
    Index("ix_aion_provenance_links_created_at", "created_at"),
)

aion_audit_verification_runs = Table(
    "aion_audit_verification_runs",
    audit_integrity_metadata,
    Column("audit_verification_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("from_sequence", BigInteger, nullable=True),
    Column("to_sequence", BigInteger, nullable=True),
    Column("checked_count", Integer, nullable=False),
    Column("valid_count", Integer, nullable=False),
    Column("invalid_count", Integer, nullable=False),
    Column("missing_count", Integer, nullable=False),
    Column("violations", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_audit_verification_trace_id", "trace_id"),
    Index("ix_aion_audit_verification_status", "status"),
    Index("ix_aion_audit_verification_from_sequence", "from_sequence"),
    Index("ix_aion_audit_verification_to_sequence", "to_sequence"),
    Index("ix_aion_audit_verification_created_at", "created_at"),
)

aion_audit_export_records = Table(
    "aion_audit_export_records",
    audit_integrity_metadata,
    Column("audit_export_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("export_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("from_sequence", BigInteger, nullable=True),
    Column("to_sequence", BigInteger, nullable=True),
    Column("filters", json_payload_type, nullable=False),
    Column("redaction_mode", Text, nullable=False),
    Column("output_ref", Text, nullable=True),
    Column("file_count", Integer, nullable=False),
    Column("entry_count", Integer, nullable=False),
    Column("checksum", Text, nullable=True),
    Column("result", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_audit_export_trace_id", "trace_id"),
    Index("ix_aion_audit_export_export_type", "export_type"),
    Index("ix_aion_audit_export_status", "status"),
    Index("ix_aion_audit_export_redaction_mode", "redaction_mode"),
    Index("ix_aion_audit_export_created_at", "created_at"),
)


class AuditIntegrityRepository:
    """Store local append-only audit integrity records."""

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

    def append_entry(self, entry: AuditEntry) -> AuditEntry:
        """Insert an audit entry without replacing existing rows."""
        values = _model_values(entry, timestamp_fields=("created_at",))
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(insert(aion_audit_entries).values(**values))
        return AuditEntry(**values)

    def get_entry(self, audit_entry_id: str) -> AuditEntry | None:
        row = self._first(
            select(aion_audit_entries).where(
                aion_audit_entries.c.audit_entry_id == audit_entry_id
            )
        )
        return _row_to_model(row, AuditEntry) if row else None

    def get_by_sequence(self, sequence_number: int) -> AuditEntry | None:
        row = self._first(
            select(aion_audit_entries).where(
                aion_audit_entries.c.sequence_number == sequence_number
            )
        )
        return _row_to_model(row, AuditEntry) if row else None

    def latest_entry(self) -> AuditEntry | None:
        row = self._first(
            select(aion_audit_entries).order_by(aion_audit_entries.c.sequence_number.desc())
        )
        return _row_to_model(row, AuditEntry) if row else None

    def list_entries(
        self,
        *,
        trace_id: str | None = None,
        resource_type: str | None = None,
        action_type: str | None = None,
        from_sequence: int | None = None,
        to_sequence: int | None = None,
        limit: int = 100,
        ascending: bool = False,
    ) -> list[AuditEntry]:
        statement = select(aion_audit_entries)
        if trace_id:
            statement = statement.where(aion_audit_entries.c.trace_id == trace_id)
        if resource_type:
            statement = statement.where(aion_audit_entries.c.resource_type == resource_type)
        if action_type:
            statement = statement.where(aion_audit_entries.c.action_type == action_type)
        if from_sequence is not None:
            statement = statement.where(aion_audit_entries.c.sequence_number >= from_sequence)
        if to_sequence is not None:
            statement = statement.where(aion_audit_entries.c.sequence_number <= to_sequence)
        order = (
            aion_audit_entries.c.sequence_number.asc()
            if ascending
            else aion_audit_entries.c.sequence_number.desc()
        )
        rows = self._list(statement.order_by(order).limit(limit))
        return [_row_to_model(row, AuditEntry) for row in rows]

    def save_checkpoint(self, checkpoint: AuditIntegrityCheckpoint) -> AuditIntegrityCheckpoint:
        values = _model_values(checkpoint, timestamp_fields=("created_at",))
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(insert(aion_audit_integrity_checkpoints).values(**values))
        return AuditIntegrityCheckpoint(**values)

    def get_checkpoint(self, checkpoint_id: str) -> AuditIntegrityCheckpoint | None:
        row = self._first(
            select(aion_audit_integrity_checkpoints).where(
                aion_audit_integrity_checkpoints.c.checkpoint_id == checkpoint_id
            )
        )
        return _row_to_model(row, AuditIntegrityCheckpoint) if row else None

    def latest_checkpoint(self) -> AuditIntegrityCheckpoint | None:
        row = self._first(
            select(aion_audit_integrity_checkpoints).order_by(
                aion_audit_integrity_checkpoints.c.created_at.desc()
            )
        )
        return _row_to_model(row, AuditIntegrityCheckpoint) if row else None

    def list_checkpoints(self, *, limit: int = 50) -> list[AuditIntegrityCheckpoint]:
        rows = self._list(
            select(aion_audit_integrity_checkpoints)
            .order_by(aion_audit_integrity_checkpoints.c.created_at.desc())
            .limit(limit)
        )
        return [_row_to_model(row, AuditIntegrityCheckpoint) for row in rows]

    def save_provenance_link(self, link: ProvenanceLink) -> ProvenanceLink:
        values = _model_values(link, timestamp_fields=("created_at",))
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(insert(aion_provenance_links).values(**values))
        return ProvenanceLink(**values)

    def get_provenance_link(self, provenance_link_id: str) -> ProvenanceLink | None:
        row = self._first(
            select(aion_provenance_links).where(
                aion_provenance_links.c.provenance_link_id == provenance_link_id
            )
        )
        return _row_to_model(row, ProvenanceLink) if row else None

    def list_provenance_links(
        self,
        *,
        source_type: str | None = None,
        source_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        trace_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[ProvenanceLink]:
        statement = select(aion_provenance_links)
        if not include_deleted:
            statement = statement.where(aion_provenance_links.c.deleted_at.is_(None))
        if source_type:
            statement = statement.where(aion_provenance_links.c.source_type == source_type)
        if source_id:
            statement = statement.where(aion_provenance_links.c.source_id == source_id)
        if target_type:
            statement = statement.where(aion_provenance_links.c.target_type == target_type)
        if target_id:
            statement = statement.where(aion_provenance_links.c.target_id == target_id)
        if trace_id:
            statement = statement.where(aion_provenance_links.c.trace_id == trace_id)
        rows = self._list(
            statement.order_by(aion_provenance_links.c.created_at.desc()).limit(limit)
        )
        return [_row_to_model(row, ProvenanceLink) for row in rows]

    def soft_delete_provenance_link(
        self,
        provenance_link_id: str,
        *,
        deleted_at: datetime,
        metadata: dict[str, Any],
    ) -> bool:
        self._ensure_schema()
        with self._engine.begin() as connection:
            result = connection.execute(
                update(aion_provenance_links)
                .where(aion_provenance_links.c.provenance_link_id == provenance_link_id)
                .where(aion_provenance_links.c.deleted_at.is_(None))
                .values(deleted_at=deleted_at, metadata=metadata)
            )
        return bool(result.rowcount)

    def save_verification_run(self, run: AuditVerificationRun) -> AuditVerificationRun:
        values = _model_values(run, timestamp_fields=("created_at", "completed_at"))
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(insert(aion_audit_verification_runs).values(**values))
        return AuditVerificationRun(**values)

    def get_verification_run(self, audit_verification_id: str) -> AuditVerificationRun | None:
        row = self._first(
            select(aion_audit_verification_runs).where(
                aion_audit_verification_runs.c.audit_verification_id
                == audit_verification_id
            )
        )
        return _row_to_model(row, AuditVerificationRun) if row else None

    def latest_verification_run(self) -> AuditVerificationRun | None:
        row = self._first(
            select(aion_audit_verification_runs).order_by(
                aion_audit_verification_runs.c.created_at.desc()
            )
        )
        return _row_to_model(row, AuditVerificationRun) if row else None

    def save_export_record(self, record: AuditExportRecord) -> AuditExportRecord:
        values = _model_values(record, timestamp_fields=("created_at", "completed_at"))
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(insert(aion_audit_export_records).values(**values))
        return AuditExportRecord(**values)

    def get_export_record(self, audit_export_id: str) -> AuditExportRecord | None:
        row = self._first(
            select(aion_audit_export_records).where(
                aion_audit_export_records.c.audit_export_id == audit_export_id
            )
        )
        return _row_to_model(row, AuditExportRecord) if row else None

    def _first(self, statement: Any) -> RowMapping | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            return connection.execute(statement).mappings().first()

    def _list(self, statement: Any) -> list[RowMapping]:
        self._ensure_schema()
        with self._engine.connect() as connection:
            return list(connection.execute(statement).mappings().all())

    def _ensure_schema(self) -> None:
        if not self._schema_ready and self._auto_create:
            audit_integrity_metadata.create_all(self._engine)
            self._schema_ready = True


def _model_values[
    ModelT: (
        AuditEntry,
        AuditIntegrityCheckpoint,
        ProvenanceLink,
        AuditVerificationRun,
        AuditExportRecord,
    )
](
    model: ModelT,
    *,
    timestamp_fields: tuple[str, ...],
) -> dict[str, Any]:
    now = datetime.now(UTC)
    values = model.model_dump(mode="python", exclude=set(timestamp_fields))
    for field in timestamp_fields:
        values[field] = getattr(model, field) or now
    return values


def _row_to_model[
    ModelT: (
        AuditEntry,
        AuditIntegrityCheckpoint,
        ProvenanceLink,
        AuditVerificationRun,
        AuditExportRecord,
    )
](row: RowMapping, model: type[ModelT]) -> ModelT:
    return model(**dict(row))
