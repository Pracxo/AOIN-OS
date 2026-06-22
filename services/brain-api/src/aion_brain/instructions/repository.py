"""Persistence for instruction hierarchy and preference ledger records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
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

from aion_brain.contracts.instructions import (
    ConstraintRecord,
    ConstraintStatus,
    ConstraintType,
    InstructionConflict,
    InstructionConflictStatus,
    InstructionConflictType,
    InstructionRecord,
    InstructionScopeType,
    InstructionSeverity,
    InstructionSourceType,
    InstructionStatus,
    InstructionType,
    StyleProfile,
    StyleProfileStatus,
)
from aion_brain.contracts.preferences import (
    PreferenceLearningCandidate,
    PreferenceLearningCandidateStatus,
    PreferenceRecord,
    PreferenceSourceType,
    PreferenceStatus,
    PreferenceType,
)

instruction_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_instruction_records = Table(
    "aion_instruction_records",
    instruction_metadata,
    Column("instruction_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("instruction_text", Text, nullable=False),
    Column("normalized_instruction", Text, nullable=False),
    Column("instruction_type", Text, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=True),
    Column("scope_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("priority", Integer, nullable=False),
    Column("status", Text, nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=True),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_instruction_records_trace_id", "trace_id"),
    Index("ix_aion_instruction_records_actor_id", "actor_id"),
    Index("ix_aion_instruction_records_workspace_id", "workspace_id"),
    Index("ix_aion_instruction_records_instruction_type", "instruction_type"),
    Index("ix_aion_instruction_records_source_type", "source_type"),
    Index("ix_aion_instruction_records_scope_type", "scope_type"),
    Index("ix_aion_instruction_records_priority", "priority"),
    Index("ix_aion_instruction_records_status", "status"),
    Index("ix_aion_instruction_records_created_at", "created_at"),
    Index("ix_aion_instruction_records_expires_at", "expires_at"),
)

aion_preference_records = Table(
    "aion_preference_records",
    instruction_metadata,
    Column("preference_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("preference_key", Text, nullable=False),
    Column("preference_type", Text, nullable=False),
    Column("preference_value", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("confirmed_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("confirmed_at", DateTime(timezone=True), nullable=True),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_preference_records_trace_id", "trace_id"),
    Index("ix_aion_preference_records_actor_id", "actor_id"),
    Index("ix_aion_preference_records_workspace_id", "workspace_id"),
    Index("ix_aion_preference_records_preference_type", "preference_type"),
    Index("ix_aion_preference_records_preference_key", "preference_key"),
    Index("ix_aion_preference_records_status", "status"),
    Index("ix_aion_preference_records_confidence", "confidence"),
    Index("ix_aion_preference_records_source_type", "source_type"),
    Index("ix_aion_preference_records_created_at", "created_at"),
)

aion_constraint_records = Table(
    "aion_constraint_records",
    instruction_metadata,
    Column("constraint_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("constraint_key", Text, nullable=False),
    Column("constraint_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("rule", json_payload_type, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_constraint_records_trace_id", "trace_id"),
    Index("ix_aion_constraint_records_actor_id", "actor_id"),
    Index("ix_aion_constraint_records_workspace_id", "workspace_id"),
    Index("ix_aion_constraint_records_constraint_type", "constraint_type"),
    Index("ix_aion_constraint_records_constraint_key", "constraint_key"),
    Index("ix_aion_constraint_records_status", "status"),
    Index("ix_aion_constraint_records_severity", "severity"),
    Index("ix_aion_constraint_records_source_type", "source_type"),
    Index("ix_aion_constraint_records_created_at", "created_at"),
)

aion_style_profiles = Table(
    "aion_style_profiles",
    instruction_metadata,
    Column("style_profile_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("style_rules", json_payload_type, nullable=False),
    Column("formatting_rules", json_payload_type, nullable=False),
    Column("tone_rules", json_payload_type, nullable=False),
    Column("prohibited_patterns", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_style_profiles_name", "name"),
    Index("ix_aion_style_profiles_workspace_id", "workspace_id"),
    Index("ix_aion_style_profiles_actor_id", "actor_id"),
    Index("ix_aion_style_profiles_status", "status"),
    Index("ix_aion_style_profiles_created_at", "created_at"),
)

aion_instruction_conflicts = Table(
    "aion_instruction_conflicts",
    instruction_metadata,
    Column("conflict_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("conflict_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("instruction_ids", json_payload_type, nullable=False),
    Column("preference_ids", json_payload_type, nullable=False),
    Column("constraint_ids", json_payload_type, nullable=False),
    Column("reason", Text, nullable=False),
    Column("resolution", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_instruction_conflicts_trace_id", "trace_id"),
    Index("ix_aion_instruction_conflicts_actor_id", "actor_id"),
    Index("ix_aion_instruction_conflicts_workspace_id", "workspace_id"),
    Index("ix_aion_instruction_conflicts_conflict_type", "conflict_type"),
    Index("ix_aion_instruction_conflicts_severity", "severity"),
    Index("ix_aion_instruction_conflicts_status", "status"),
    Index("ix_aion_instruction_conflicts_created_at", "created_at"),
)

aion_instruction_resolution_runs = Table(
    "aion_instruction_resolution_runs",
    instruction_metadata,
    Column("resolution_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("input", json_payload_type, nullable=False),
    Column("applied_instruction_ids", json_payload_type, nullable=False),
    Column("applied_preference_ids", json_payload_type, nullable=False),
    Column("applied_constraint_ids", json_payload_type, nullable=False),
    Column("suppressed_instruction_ids", json_payload_type, nullable=False),
    Column("conflict_ids", json_payload_type, nullable=False),
    Column("effective_instructions", json_payload_type, nullable=False),
    Column("effective_style", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_instruction_resolution_runs_trace_id", "trace_id"),
    Index("ix_aion_instruction_resolution_runs_actor_id", "actor_id"),
    Index("ix_aion_instruction_resolution_runs_workspace_id", "workspace_id"),
    Index("ix_aion_instruction_resolution_runs_status", "status"),
    Index("ix_aion_instruction_resolution_runs_created_at", "created_at"),
)

aion_preference_learning_candidates = Table(
    "aion_preference_learning_candidates",
    instruction_metadata,
    Column("candidate_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("preference_key", Text, nullable=False),
    Column("preference_type", Text, nullable=False),
    Column("proposed_value", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("reason", Text, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=True),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_preference_learning_candidates_trace_id", "trace_id"),
    Index("ix_aion_preference_learning_candidates_actor_id", "actor_id"),
    Index("ix_aion_preference_learning_candidates_workspace_id", "workspace_id"),
    Index("ix_aion_preference_learning_candidates_preference_type", "preference_type"),
    Index("ix_aion_preference_learning_candidates_preference_key", "preference_key"),
    Index("ix_aion_preference_learning_candidates_status", "status"),
    Index("ix_aion_preference_learning_candidates_created_at", "created_at"),
)


class InstructionRepository:
    """Repository for instructions, preferences, constraints, styles, and conflicts."""

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

    def save_instruction(self, record: InstructionRecord) -> InstructionRecord:
        stored = record.model_copy(
            update={
                "created_at": record.created_at or datetime.now(UTC),
                "updated_at": record.updated_at or datetime.now(UTC),
            }
        )
        self._replace(aion_instruction_records, "instruction_id", stored.instruction_id, stored)
        return stored

    def get_instruction(self, instruction_id: str) -> InstructionRecord | None:
        return self._get(
            aion_instruction_records,
            "instruction_id",
            instruction_id,
            _row_to_instruction,
        )

    def list_instructions(
        self,
        *,
        scope: list[str] | None = None,
        status: str | None = None,
        instruction_type: str | None = None,
        scope_type: str | None = None,
        limit: int = 100,
    ) -> list[InstructionRecord]:
        statement = select(aion_instruction_records)
        if status:
            statement = statement.where(aion_instruction_records.c.status == status)
        if instruction_type:
            statement = statement.where(
                aion_instruction_records.c.instruction_type == instruction_type
            )
        if scope_type:
            statement = statement.where(aion_instruction_records.c.scope_type == scope_type)
        rows = self._rows(
            statement.order_by(
                aion_instruction_records.c.priority.desc(),
                aion_instruction_records.c.created_at.desc(),
            ).limit(limit)
        )
        return _filter_scope([_row_to_instruction(row) for row in rows], scope)[:limit]

    def save_preference(self, record: PreferenceRecord) -> PreferenceRecord:
        stored = record.model_copy(
            update={
                "created_at": record.created_at or datetime.now(UTC),
                "updated_at": record.updated_at or datetime.now(UTC),
            }
        )
        self._replace(aion_preference_records, "preference_id", stored.preference_id, stored)
        return stored

    def get_preference(self, preference_id: str) -> PreferenceRecord | None:
        return self._get(
            aion_preference_records,
            "preference_id",
            preference_id,
            _row_to_preference,
        )

    def list_preferences(
        self,
        *,
        scope: list[str] | None = None,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
        preference_type: str | None = None,
        limit: int = 100,
    ) -> list[PreferenceRecord]:
        statement = select(aion_preference_records)
        if actor_id:
            statement = statement.where(aion_preference_records.c.actor_id == actor_id)
        if workspace_id:
            statement = statement.where(aion_preference_records.c.workspace_id == workspace_id)
        if status:
            statement = statement.where(aion_preference_records.c.status == status)
        if preference_type:
            statement = statement.where(
                aion_preference_records.c.preference_type == preference_type
            )
        rows = self._rows(
            statement.order_by(
                aion_preference_records.c.confidence.desc(),
                aion_preference_records.c.created_at.desc(),
            ).limit(limit)
        )
        return _filter_scope([_row_to_preference(row) for row in rows], scope)[:limit]

    def save_constraint(self, record: ConstraintRecord) -> ConstraintRecord:
        stored = record.model_copy(
            update={
                "created_at": record.created_at or datetime.now(UTC),
                "updated_at": record.updated_at or datetime.now(UTC),
            }
        )
        self._replace(aion_constraint_records, "constraint_id", stored.constraint_id, stored)
        return stored

    def get_constraint(self, constraint_id: str) -> ConstraintRecord | None:
        return self._get(
            aion_constraint_records,
            "constraint_id",
            constraint_id,
            _row_to_constraint,
        )

    def list_constraints(
        self,
        *,
        scope: list[str] | None = None,
        status: str | None = None,
        constraint_type: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[ConstraintRecord]:
        statement = select(aion_constraint_records)
        if status:
            statement = statement.where(aion_constraint_records.c.status == status)
        if constraint_type:
            statement = statement.where(
                aion_constraint_records.c.constraint_type == constraint_type
            )
        if severity:
            statement = statement.where(aion_constraint_records.c.severity == severity)
        rows = self._rows(
            statement.order_by(aion_constraint_records.c.created_at.desc()).limit(limit)
        )
        return _filter_scope([_row_to_constraint(row) for row in rows], scope)[:limit]

    def save_style_profile(self, profile: StyleProfile) -> StyleProfile:
        stored = profile.model_copy(
            update={
                "created_at": profile.created_at or datetime.now(UTC),
                "updated_at": profile.updated_at or datetime.now(UTC),
            }
        )
        self._replace(aion_style_profiles, "style_profile_id", stored.style_profile_id, stored)
        return stored

    def get_style_profile(self, style_profile_id: str) -> StyleProfile | None:
        return self._get(
            aion_style_profiles,
            "style_profile_id",
            style_profile_id,
            _row_to_style_profile,
        )

    def list_style_profiles(
        self,
        *,
        scope: list[str] | None = None,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[StyleProfile]:
        statement = select(aion_style_profiles)
        if actor_id:
            statement = statement.where(aion_style_profiles.c.actor_id == actor_id)
        if workspace_id:
            statement = statement.where(aion_style_profiles.c.workspace_id == workspace_id)
        if status:
            statement = statement.where(aion_style_profiles.c.status == status)
        rows = self._rows(statement.order_by(aion_style_profiles.c.created_at.desc()).limit(limit))
        return _filter_scope([_row_to_style_profile(row) for row in rows], scope)[:limit]

    def save_conflict(self, conflict: InstructionConflict) -> InstructionConflict:
        stored = conflict.model_copy(
            update={"created_at": conflict.created_at or datetime.now(UTC)}
        )
        self._replace(aion_instruction_conflicts, "conflict_id", stored.conflict_id, stored)
        return stored

    def get_conflict(self, conflict_id: str) -> InstructionConflict | None:
        return self._get(aion_instruction_conflicts, "conflict_id", conflict_id, _row_to_conflict)

    def list_conflicts(
        self,
        *,
        scope: list[str] | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[InstructionConflict]:
        statement = select(aion_instruction_conflicts)
        if status:
            statement = statement.where(aion_instruction_conflicts.c.status == status)
        if severity:
            statement = statement.where(aion_instruction_conflicts.c.severity == severity)
        rows = self._rows(
            statement.order_by(aion_instruction_conflicts.c.created_at.desc()).limit(limit)
        )
        return _filter_scope([_row_to_conflict(row) for row in rows], scope)[:limit]

    def save_resolution_run(
        self,
        *,
        resolution_run_id: str,
        trace_id: str | None,
        actor_id: str | None,
        workspace_id: str | None,
        owner_scope: list[str],
        request: dict[str, Any],
        result: dict[str, Any],
        status: str,
    ) -> None:
        self._ensure_schema()
        values = {
            "resolution_run_id": resolution_run_id,
            "trace_id": trace_id,
            "actor_id": actor_id,
            "workspace_id": workspace_id,
            "status": status,
            "owner_scope": owner_scope,
            "input": request,
            "applied_instruction_ids": result.get("applied_instruction_ids", []),
            "applied_preference_ids": result.get("applied_preference_ids", []),
            "applied_constraint_ids": result.get("applied_constraint_ids", []),
            "suppressed_instruction_ids": result.get("suppressed_instruction_ids", []),
            "conflict_ids": [
                item.get("conflict_id")
                for item in result.get("conflicts", [])
                if isinstance(item, dict) and item.get("conflict_id")
            ],
            "effective_instructions": result.get("effective_instructions", []),
            "effective_style": result.get("effective_style", {}),
            "constraints": result.get("constraints", []),
            "result": result,
            "created_by": result.get("created_by"),
            "created_at": datetime.now(UTC),
            "completed_at": datetime.now(UTC),
        }
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_instruction_resolution_runs).where(
                    aion_instruction_resolution_runs.c.resolution_run_id == resolution_run_id
                )
            )
            connection.execute(insert(aion_instruction_resolution_runs).values(**values))

    def save_candidate(self, candidate: PreferenceLearningCandidate) -> PreferenceLearningCandidate:
        stored = candidate.model_copy(
            update={"created_at": candidate.created_at or datetime.now(UTC)}
        )
        self._replace(
            aion_preference_learning_candidates,
            "candidate_id",
            stored.candidate_id,
            stored,
        )
        return stored

    def get_candidate(self, candidate_id: str) -> PreferenceLearningCandidate | None:
        return self._get(
            aion_preference_learning_candidates,
            "candidate_id",
            candidate_id,
            _row_to_candidate,
        )

    def list_candidates(
        self,
        *,
        scope: list[str] | None = None,
        status: str | None = None,
        preference_type: str | None = None,
        limit: int = 100,
    ) -> list[PreferenceLearningCandidate]:
        statement = select(aion_preference_learning_candidates)
        if status:
            statement = statement.where(aion_preference_learning_candidates.c.status == status)
        if preference_type:
            statement = statement.where(
                aion_preference_learning_candidates.c.preference_type == preference_type
            )
        rows = self._rows(
            statement.order_by(aion_preference_learning_candidates.c.created_at.desc()).limit(limit)
        )
        return _filter_scope([_row_to_candidate(row) for row in rows], scope)[:limit]

    def _replace(self, table: Table, key: str, value: str, model: object) -> None:
        self._ensure_schema()
        values = _table_values(table.name, model)
        with self._engine.begin() as connection:
            connection.execute(delete(table).where(table.c[key] == value))
            connection.execute(insert(table).values(**values))

    def _get[T](self, table: Table, key: str, value: str, mapper: object) -> T | None:
        rows = self._rows(select(table).where(table.c[key] == value).limit(1))
        if not rows:
            return None
        return cast(T, cast(Any, mapper)(rows[0]))

    def _rows(self, statement: object) -> list[RowMapping]:
        self._ensure_schema()
        with self._engine.connect() as connection:
            return list(connection.execute(cast(Any, statement)).mappings().all())

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        instruction_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_instruction(row: RowMapping) -> InstructionRecord:
    return InstructionRecord(
        instruction_id=str(row["instruction_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        instruction_text=str(row["instruction_text"]),
        normalized_instruction=_optional_str(row["normalized_instruction"]),
        instruction_type=cast(InstructionType, str(row["instruction_type"])),
        source_type=cast(InstructionSourceType, str(row["source_type"])),
        source_id=_optional_str(row["source_id"]),
        scope_type=cast(InstructionScopeType, str(row["scope_type"])),
        owner_scope=_string_list(row["owner_scope"]),
        priority=int(row["priority"]),
        status=cast(InstructionStatus, str(row["status"])),
        expires_at=_optional_datetime(row["expires_at"]),
        constraints=_string_list(row["constraints"]),
        metadata=_dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _row_to_preference(row: RowMapping) -> PreferenceRecord:
    return PreferenceRecord(
        preference_id=str(row["preference_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        preference_type=cast(PreferenceType, str(row["preference_type"])),
        preference_key=str(row["preference_key"]),
        preference_value=_dict(row["preference_value"]),
        confidence=float(row["confidence"]),
        status=cast(PreferenceStatus, str(row["status"])),
        source_type=cast(PreferenceSourceType, str(row["source_type"])),
        source_id=_optional_str(row["source_id"]),
        owner_scope=_string_list(row["owner_scope"]),
        evidence_refs=_string_list(row["evidence_refs"]),
        metadata=_dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        confirmed_by=_optional_str(row["confirmed_by"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        confirmed_at=_optional_datetime(row["confirmed_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _row_to_constraint(row: RowMapping) -> ConstraintRecord:
    return ConstraintRecord(
        constraint_id=str(row["constraint_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        constraint_key=str(row["constraint_key"]),
        constraint_type=cast(ConstraintType, str(row["constraint_type"])),
        status=cast(ConstraintStatus, str(row["status"])),
        severity=cast(InstructionSeverity, str(row["severity"])),
        description=str(row["description"]),
        rule=_dict(row["rule"]),
        source_type=cast(InstructionSourceType, str(row["source_type"])),
        source_id=_optional_str(row["source_id"]),
        owner_scope=_string_list(row["owner_scope"]),
        metadata=_dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _row_to_style_profile(row: RowMapping) -> StyleProfile:
    return StyleProfile(
        style_profile_id=str(row["style_profile_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(StyleProfileStatus, str(row["status"])),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        owner_scope=_string_list(row["owner_scope"]),
        style_rules=_dict(row["style_rules"]),
        formatting_rules=_dict(row["formatting_rules"]),
        tone_rules=_dict(row["tone_rules"]),
        prohibited_patterns=_string_list(row["prohibited_patterns"]),
        metadata=_dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _row_to_conflict(row: RowMapping) -> InstructionConflict:
    return InstructionConflict(
        conflict_id=str(row["conflict_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        conflict_type=cast(InstructionConflictType, str(row["conflict_type"])),
        severity=cast(InstructionSeverity, str(row["severity"])),
        status=cast(InstructionConflictStatus, str(row["status"])),
        owner_scope=_string_list(row["owner_scope"]),
        instruction_ids=_string_list(row["instruction_ids"]),
        preference_ids=_string_list(row["preference_ids"]),
        constraint_ids=_string_list(row["constraint_ids"]),
        reason=str(row["reason"]),
        resolution=_optional_str(row["resolution"]),
        metadata=_dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
        resolved_at=_optional_datetime(row["resolved_at"]),
    )


def _row_to_candidate(row: RowMapping) -> PreferenceLearningCandidate:
    return PreferenceLearningCandidate(
        candidate_id=str(row["candidate_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        preference_key=str(row["preference_key"]),
        preference_type=cast(PreferenceType, str(row["preference_type"])),
        proposed_value=_dict(row["proposed_value"]),
        status=cast(PreferenceLearningCandidateStatus, str(row["status"])),
        confidence=float(row["confidence"]),
        reason=str(row["reason"]),
        source_type=cast(PreferenceSourceType, str(row["source_type"])),
        source_id=_optional_str(row["source_id"]),
        evidence_refs=_string_list(row["evidence_refs"]),
        owner_scope=_string_list(row["owner_scope"]),
        metadata=_dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        resolved_at=_optional_datetime(row["resolved_at"]),
    )


def _dict(value: object) -> dict[str, Any]:
    return cast(dict[str, Any], value) if isinstance(value, dict) else {}


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _table_values(table_name: str, model: object) -> dict[str, Any]:
    dumped = cast(Any, model).model_dump(mode="python")
    if table_name == "aion_instruction_records":
        return {
            "instruction_id": dumped["instruction_id"],
            "trace_id": dumped.get("trace_id"),
            "actor_id": dumped.get("actor_id"),
            "workspace_id": dumped.get("workspace_id"),
            "instruction_text": dumped["instruction_text"],
            "normalized_instruction": dumped.get("normalized_instruction")
            or dumped["instruction_text"],
            "instruction_type": dumped["instruction_type"],
            "source_type": dumped.get("source_type", "generic"),
            "source_id": dumped.get("source_id"),
            "scope_type": dumped["scope_type"],
            "owner_scope": dumped["owner_scope"],
            "priority": dumped.get("priority", 500),
            "status": dumped["status"],
            "expires_at": dumped.get("expires_at"),
            "constraints": dumped.get("constraints", []),
            "metadata": dumped.get("metadata", {}),
            "created_by": dumped.get("created_by"),
            "created_at": dumped.get("created_at"),
            "updated_at": dumped.get("updated_at"),
            "disabled_at": dumped.get("disabled_at"),
        }
    if table_name == "aion_preference_records":
        return {
            "preference_id": dumped["preference_id"],
            "trace_id": dumped.get("trace_id"),
            "actor_id": dumped.get("actor_id"),
            "workspace_id": dumped.get("workspace_id"),
            "preference_type": dumped["preference_type"],
            "preference_key": dumped["preference_key"],
            "preference_value": dumped.get("preference_value", {}),
            "confidence": dumped["confidence"],
            "status": dumped["status"],
            "source_type": dumped.get("source_type", "generic"),
            "source_id": dumped.get("source_id"),
            "owner_scope": dumped["owner_scope"],
            "evidence_refs": dumped.get("evidence_refs", []),
            "metadata": dumped.get("metadata", {}),
            "created_by": dumped.get("created_by"),
            "confirmed_by": dumped.get("confirmed_by"),
            "created_at": dumped.get("created_at"),
            "updated_at": dumped.get("updated_at"),
            "confirmed_at": dumped.get("confirmed_at"),
            "disabled_at": dumped.get("disabled_at"),
        }
    if table_name == "aion_constraint_records":
        return {
            "constraint_id": dumped["constraint_id"],
            "trace_id": dumped.get("trace_id"),
            "actor_id": dumped.get("actor_id"),
            "workspace_id": dumped.get("workspace_id"),
            "constraint_key": dumped["constraint_key"],
            "constraint_type": dumped["constraint_type"],
            "status": dumped["status"],
            "severity": dumped["severity"],
            "description": dumped["description"],
            "rule": dumped.get("rule", {}),
            "source_type": dumped.get("source_type", "generic"),
            "source_id": dumped.get("source_id"),
            "owner_scope": dumped["owner_scope"],
            "metadata": dumped.get("metadata", {}),
            "created_by": dumped.get("created_by"),
            "created_at": dumped.get("created_at"),
            "updated_at": dumped.get("updated_at"),
            "disabled_at": dumped.get("disabled_at"),
        }
    if table_name == "aion_style_profiles":
        return {
            "style_profile_id": dumped["style_profile_id"],
            "name": dumped["name"],
            "description": dumped["description"],
            "status": dumped["status"],
            "actor_id": dumped.get("actor_id"),
            "workspace_id": dumped.get("workspace_id"),
            "owner_scope": dumped["owner_scope"],
            "style_rules": dumped.get("style_rules", {}),
            "formatting_rules": dumped.get("formatting_rules", {}),
            "tone_rules": dumped.get("tone_rules", {}),
            "prohibited_patterns": dumped.get("prohibited_patterns", []),
            "metadata": dumped.get("metadata", {}),
            "created_by": dumped.get("created_by"),
            "created_at": dumped.get("created_at"),
            "updated_at": dumped.get("updated_at"),
            "disabled_at": dumped.get("disabled_at"),
        }
    if table_name == "aion_instruction_conflicts":
        return {
            "conflict_id": dumped["conflict_id"],
            "trace_id": dumped.get("trace_id"),
            "actor_id": dumped.get("actor_id"),
            "workspace_id": dumped.get("workspace_id"),
            "conflict_type": dumped["conflict_type"],
            "severity": dumped["severity"],
            "status": dumped["status"],
            "owner_scope": dumped["owner_scope"],
            "instruction_ids": dumped.get("instruction_ids", []),
            "preference_ids": dumped.get("preference_ids", []),
            "constraint_ids": dumped.get("constraint_ids", []),
            "reason": dumped["reason"],
            "resolution": dumped.get("resolution"),
            "metadata": dumped.get("metadata", {}),
            "created_at": dumped.get("created_at"),
            "resolved_at": dumped.get("resolved_at"),
        }
    if table_name == "aion_preference_learning_candidates":
        return {
            "candidate_id": dumped["candidate_id"],
            "trace_id": dumped.get("trace_id"),
            "actor_id": dumped.get("actor_id"),
            "workspace_id": dumped.get("workspace_id"),
            "preference_key": dumped["preference_key"],
            "preference_type": dumped["preference_type"],
            "proposed_value": dumped.get("proposed_value", {}),
            "status": dumped["status"],
            "confidence": dumped["confidence"],
            "reason": dumped["reason"],
            "source_type": dumped.get("source_type", "generic"),
            "source_id": dumped.get("source_id"),
            "evidence_refs": dumped.get("evidence_refs", []),
            "owner_scope": dumped["owner_scope"],
            "metadata": dumped.get("metadata", {}),
            "created_by": dumped.get("created_by"),
            "created_at": dumped.get("created_at"),
            "resolved_at": dumped.get("resolved_at"),
        }
    return cast(dict[str, Any], dumped)


def _record_precedence_rank(model: object) -> int:
    instruction_type = str(getattr(model, "instruction_type", "generic"))
    source_type = str(getattr(model, "source_type", "generic"))
    if instruction_type in {"policy", "safety"} or source_type == "policy":
        return 1
    if instruction_type == "runtime" or source_type == "runtime_config":
        return 2
    if instruction_type == "capability":
        return 5
    if instruction_type == "session_instruction":
        return 6
    if instruction_type in {"task_instruction", "workflow"}:
        return 7
    if instruction_type == "workspace_instruction":
        return 8
    if instruction_type in {"actor_preference", "learned_candidate"}:
        return 9
    return 8


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return datetime.now(UTC)


def _optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    return _datetime(value)


def _filter_scope[T](records: list[T], scope: list[str] | None) -> list[T]:
    if not scope:
        return records
    requested = set(scope)
    filtered: list[T] = []
    for record in records:
        owner_scope = set(getattr(record, "owner_scope", []))
        if not owner_scope or requested.intersection(owner_scope):
            filtered.append(record)
    return filtered


__all__ = ["InstructionRepository"]
