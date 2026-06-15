"""Persistent reflection repository."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
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
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.reflection import ReflectionRecord, ReflectionStatus, ReflectionType

reflection_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_reflections = Table(
    "aion_reflections",
    reflection_metadata,
    Column("reflection_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("task_id", Text, nullable=True),
    Column("task_run_id", Text, nullable=True),
    Column("execution_id", Text, nullable=True),
    Column("evaluation_id", Text, nullable=True),
    Column("learning_signal_ids", json_payload_type, nullable=False),
    Column("reflection_type", Text, nullable=False),
    Column("observations", json_payload_type, nullable=False),
    Column("proposed_changes", json_payload_type, nullable=False),
    Column("risks", json_payload_type, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_reflections_trace_id", "trace_id"),
    Index("ix_aion_reflections_task_id", "task_id"),
    Index("ix_aion_reflections_task_run_id", "task_run_id"),
    Index("ix_aion_reflections_execution_id", "execution_id"),
    Index("ix_aion_reflections_evaluation_id", "evaluation_id"),
    Index("ix_aion_reflections_reflection_type", "reflection_type"),
    Index("ix_aion_reflections_status", "status"),
    Index("ix_aion_reflections_created_at", "created_at"),
)


class ReflectionRepository:
    """Repository for reflection records."""

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

    def save_reflection(self, reflection: ReflectionRecord) -> ReflectionRecord:
        """Persist a reflection record."""
        self._ensure_schema()
        stored = reflection.model_copy(
            update={"created_at": reflection.created_at or datetime.now(UTC)}
        )
        with self._engine.begin() as connection:
            connection.execute(insert(aion_reflections).values(**stored.model_dump(mode="python")))
        return stored

    def get_reflection(self, reflection_id: str) -> ReflectionRecord | None:
        """Return a reflection by ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_reflections).where(aion_reflections.c.reflection_id == reflection_id)
            ).mappings().first()
        if row is None:
            return None
        return _row_to_reflection(row)

    def list_reflections(
        self,
        *,
        trace_id: str | None = None,
        task_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ReflectionRecord]:
        """List reflections by optional filters."""
        self._ensure_schema()
        statement = select(aion_reflections).order_by(aion_reflections.c.created_at.desc()).limit(
            limit
        )
        if trace_id is not None:
            statement = statement.where(aion_reflections.c.trace_id == trace_id)
        if task_id is not None:
            statement = statement.where(aion_reflections.c.task_id == task_id)
        if status is not None:
            statement = statement.where(aion_reflections.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_reflection(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        reflection_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_reflection(row: RowMapping) -> ReflectionRecord:
    return ReflectionRecord(
        reflection_id=str(row["reflection_id"]),
        trace_id=_optional_str(row["trace_id"]),
        task_id=_optional_str(row["task_id"]),
        task_run_id=_optional_str(row["task_run_id"]),
        execution_id=_optional_str(row["execution_id"]),
        evaluation_id=_optional_str(row["evaluation_id"]),
        learning_signal_ids=_str_list(row["learning_signal_ids"]),
        reflection_type=cast(ReflectionType, str(row["reflection_type"])),
        observations=_str_list(row["observations"]),
        proposed_changes=_dict_list(row["proposed_changes"]),
        risks=_str_list(row["risks"]),
        confidence=float(row["confidence"]),
        status=cast(ReflectionStatus, str(row["status"])),
        created_at=_optional_datetime(row["created_at"]),
    )


def _str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [dict(item) for item in value if isinstance(item, dict)]
    return []


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
