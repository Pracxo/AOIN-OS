"""Persistent skill registry repository."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
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
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.goals import LifecycleRiskLevel
from aion_brain.contracts.skills import (
    SkillActivationEvent,
    SkillCandidate,
    SkillCandidateStatus,
    SkillRecord,
    SkillStatus,
    SkillVersion,
)

skill_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_skill_candidates = Table(
    "aion_skill_candidates",
    skill_metadata,
    Column("candidate_id", Text, primary_key=True),
    Column("reflection_id", Text, nullable=True),
    Column("source_trace_ids", json_payload_type, nullable=False),
    Column("source_task_ids", json_payload_type, nullable=False),
    Column("source_learning_signal_ids", json_payload_type, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("trigger_patterns", json_payload_type, nullable=False),
    Column("preconditions", json_payload_type, nullable=False),
    Column("procedure_steps", json_payload_type, nullable=False),
    Column("expected_outcomes", json_payload_type, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("evaluation_summary", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_skill_candidates_reflection_id", "reflection_id"),
    Index("ix_aion_skill_candidates_name", "name"),
    Index("ix_aion_skill_candidates_risk_level", "risk_level"),
    Index("ix_aion_skill_candidates_confidence", "confidence"),
    Index("ix_aion_skill_candidates_status", "status"),
    Index("ix_aion_skill_candidates_created_at", "created_at"),
)

aion_skills = Table(
    "aion_skills",
    skill_metadata,
    Column("skill_id", Text, primary_key=True),
    Column("candidate_id", Text, nullable=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("current_version", Integer, nullable=False),
    Column("trigger_patterns", json_payload_type, nullable=False),
    Column("preconditions", json_payload_type, nullable=False),
    Column("procedure_steps", json_payload_type, nullable=False),
    Column("expected_outcomes", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("activated_at", DateTime(timezone=True), nullable=True),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_skills_candidate_id", "candidate_id"),
    Index("ix_aion_skills_name", "name"),
    Index("ix_aion_skills_status", "status"),
    Index("ix_aion_skills_risk_level", "risk_level"),
    Index("ix_aion_skills_current_version", "current_version"),
    Index("ix_aion_skills_created_at", "created_at"),
)

aion_skill_versions = Table(
    "aion_skill_versions",
    skill_metadata,
    Column("skill_version_id", Text, primary_key=True),
    Column("skill_id", Text, ForeignKey("aion_skills.skill_id"), nullable=False),
    Column("version", Integer, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("trigger_patterns", json_payload_type, nullable=False),
    Column("preconditions", json_payload_type, nullable=False),
    Column("procedure_steps", json_payload_type, nullable=False),
    Column("expected_outcomes", json_payload_type, nullable=False),
    Column("change_reason", Text, nullable=False),
    Column("source_candidate_id", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_skill_versions_skill_id", "skill_id"),
    Index("ix_aion_skill_versions_version", "version"),
    Index("ix_aion_skill_versions_source_candidate_id", "source_candidate_id"),
    Index("ix_aion_skill_versions_created_at", "created_at"),
)

aion_skill_activation_events = Table(
    "aion_skill_activation_events",
    skill_metadata,
    Column("activation_event_id", Text, primary_key=True),
    Column("skill_id", Text, nullable=False),
    Column("skill_version_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("event_type", Text, nullable=False),
    Column("from_status", Text, nullable=True),
    Column("to_status", Text, nullable=True),
    Column("reason", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("payload", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_skill_activation_events_skill_id", "skill_id"),
    Index("ix_aion_skill_activation_events_skill_version_id", "skill_version_id"),
    Index("ix_aion_skill_activation_events_trace_id", "trace_id"),
    Index("ix_aion_skill_activation_events_event_type", "event_type"),
    Index("ix_aion_skill_activation_events_from_status", "from_status"),
    Index("ix_aion_skill_activation_events_to_status", "to_status"),
    Index("ix_aion_skill_activation_events_created_at", "created_at"),
)


class SkillRepository:
    """Repository for skill candidates, skills, versions, and activation events."""

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
            self._engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_pre_ping=True,
            )
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_candidate(self, candidate: SkillCandidate) -> SkillCandidate:
        """Upsert a skill candidate."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = candidate.model_copy(
            update={
                "created_at": candidate.created_at or now,
                "updated_at": now,
            }
        )
        values = stored.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_skill_candidates.c.candidate_id).where(
                    aion_skill_candidates.c.candidate_id == stored.candidate_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_skill_candidates).values(**values))
            else:
                connection.execute(
                    update(aion_skill_candidates)
                    .where(aion_skill_candidates.c.candidate_id == stored.candidate_id)
                    .values(**values)
                )
        return stored

    def get_candidate(self, candidate_id: str) -> SkillCandidate | None:
        """Return a candidate by ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_skill_candidates).where(
                    aion_skill_candidates.c.candidate_id == candidate_id
                )
            ).mappings().first()
        if row is None:
            return None
        return _row_to_candidate(row)

    def list_candidates(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[SkillCandidate]:
        """List candidates by optional status."""
        self._ensure_schema()
        statement = select(aion_skill_candidates).order_by(
            aion_skill_candidates.c.created_at.desc()
        ).limit(limit)
        if status is not None:
            statement = statement.where(aion_skill_candidates.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_candidate(row) for row in rows]

    def save_skill(self, skill: SkillRecord) -> SkillRecord:
        """Upsert a skill record."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = skill.model_copy(
            update={
                "created_at": skill.created_at or now,
                "updated_at": now,
            }
        )
        values = stored.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_skills.c.skill_id).where(aion_skills.c.skill_id == stored.skill_id)
            ).first()
            if existing is None:
                connection.execute(insert(aion_skills).values(**values))
            else:
                connection.execute(
                    update(aion_skills)
                    .where(aion_skills.c.skill_id == stored.skill_id)
                    .values(**values)
                )
        return stored

    def get_skill(self, skill_id: str) -> SkillRecord | None:
        """Return a skill by ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_skills).where(aion_skills.c.skill_id == skill_id)
            ).mappings().first()
        if row is None:
            return None
        return _row_to_skill(row)

    def list_skills(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[SkillRecord]:
        """List skills by scope and optional status."""
        self._ensure_schema()
        statement = select(aion_skills).order_by(aion_skills.c.created_at.desc()).limit(limit)
        if status is not None:
            statement = statement.where(aion_skills.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        skills = [_row_to_skill(row) for row in rows]
        return [skill for skill in skills if _within_scope(skill.owner_scope, scope)]

    def save_version(self, version: SkillVersion) -> SkillVersion:
        """Persist a skill version."""
        self._ensure_schema()
        stored = version.model_copy(update={"created_at": version.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(insert(aion_skill_versions).values(**stored.model_dump(mode="python")))
        return stored

    def save_activation_event(self, event: SkillActivationEvent) -> SkillActivationEvent:
        """Persist a skill activation event."""
        self._ensure_schema()
        stored = event.model_copy(update={"created_at": event.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_skill_activation_events).values(**stored.model_dump(mode="python"))
            )
        return stored

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        skill_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_candidate(row: RowMapping) -> SkillCandidate:
    return SkillCandidate(
        candidate_id=str(row["candidate_id"]),
        reflection_id=_optional_str(row["reflection_id"]),
        source_trace_ids=_str_list(row["source_trace_ids"]),
        source_task_ids=_str_list(row["source_task_ids"]),
        source_learning_signal_ids=_str_list(row["source_learning_signal_ids"]),
        name=str(row["name"]),
        description=str(row["description"]),
        trigger_patterns=_str_list(row["trigger_patterns"]),
        preconditions=_str_list(row["preconditions"]),
        procedure_steps=list(row["procedure_steps"]),
        expected_outcomes=_str_list(row["expected_outcomes"]),
        risk_level=cast(LifecycleRiskLevel, str(row["risk_level"])),
        confidence=float(row["confidence"]),
        evaluation_summary=_dict(row["evaluation_summary"]),
        status=cast(SkillCandidateStatus, str(row["status"])),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
    )


def _row_to_skill(row: RowMapping) -> SkillRecord:
    return SkillRecord(
        skill_id=str(row["skill_id"]),
        candidate_id=_optional_str(row["candidate_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(SkillStatus, str(row["status"])),
        risk_level=cast(LifecycleRiskLevel, str(row["risk_level"])),
        current_version=int(row["current_version"]),
        trigger_patterns=_str_list(row["trigger_patterns"]),
        preconditions=_str_list(row["preconditions"]),
        procedure_steps=list(row["procedure_steps"]),
        expected_outcomes=_str_list(row["expected_outcomes"]),
        owner_scope=_str_list(row["owner_scope"]),
        metadata=_dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        activated_at=_optional_datetime(row["activated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _within_scope(owner_scope: list[str], scope: list[str]) -> bool:
    return not scope or any(item in owner_scope for item in scope)


def _str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")
