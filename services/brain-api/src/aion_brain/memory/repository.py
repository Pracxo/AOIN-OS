"""Canonical Postgres memory repository."""

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
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.memory import MemoryRecord, MemoryType
from aion_brain.memory.in_memory_adapter import rank_memory_records

memory_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_memory_records = Table(
    "aion_memory_records",
    memory_metadata,
    Column("memory_id", Text, primary_key=True),
    Column("memory_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("source_event_id", Text, nullable=True),
    Column("content_ref", Text, nullable=True),
    Column("summary", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("sensitivity", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_memory_records_memory_type", "memory_type"),
    Index("ix_aion_memory_records_source_event_id", "source_event_id"),
    Index("ix_aion_memory_records_created_at", "created_at"),
    Index("ix_aion_memory_records_deleted_at", "deleted_at"),
)


class MemoryRepository:
    """Canonical repository for AION memory metadata and lexical recall."""

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

    def remember(self, record: MemoryRecord) -> str:
        """Store a memory record and return its ID."""
        self.save(record)
        return record.memory_id

    def save(self, record: MemoryRecord) -> MemoryRecord:
        """Persist a memory record and return the stored contract."""
        self._ensure_schema()
        values = record.model_dump(mode="python")
        values["deleted_at"] = None

        with self._engine.begin() as connection:
            connection.execute(insert(aion_memory_records).values(**values))

        return record

    def get(self, memory_id: str) -> MemoryRecord | None:
        """Return an active memory record by ID."""
        self._ensure_schema()
        statement = select(aion_memory_records).where(
            aion_memory_records.c.memory_id == memory_id,
            aion_memory_records.c.deleted_at.is_(None),
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()

        if row is None:
            return None
        if _is_expired(_optional_datetime(row["expires_at"])):
            return None
        return self._row_to_record(row)

    def retrieve(
        self,
        query: str,
        scope: list[str],
        limit: int = 10,
        memory_types: list[MemoryType] | None = None,
    ) -> list[MemoryRecord]:
        """Retrieve active memory using deterministic lexical ranking."""
        self._ensure_schema()
        statement = select(aion_memory_records).where(aion_memory_records.c.deleted_at.is_(None))
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()

        allowed_types = set(memory_types or [])
        candidates = [
            self._row_to_record(row)
            for row in rows
            if _scope_matches(list(row["owner_scope"]), scope)
            and (not allowed_types or row["memory_type"] in allowed_types)
            and not _is_expired(_optional_datetime(row["expires_at"]))
        ]
        return rank_memory_records(query, candidates)[:limit]

    def list_active(
        self,
        scope: list[str],
        *,
        limit: int = 100,
        memory_types: list[MemoryType] | None = None,
    ) -> list[MemoryRecord]:
        """List active memory records within scope."""
        self._ensure_schema()
        statement = (
            select(aion_memory_records)
            .where(aion_memory_records.c.deleted_at.is_(None))
            .order_by(aion_memory_records.c.created_at.desc())
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()

        allowed_types = set(memory_types or [])
        records = [
            self._row_to_record(row)
            for row in rows
            if _scope_matches(list(row["owner_scope"]), scope)
            and (not allowed_types or row["memory_type"] in allowed_types)
            and not _is_expired(_optional_datetime(row["expires_at"]))
        ]
        return records[:limit]

    def forget(self, memory_id: str) -> bool:
        """Soft-delete a memory record."""
        self._ensure_schema()
        statement = (
            update(aion_memory_records)
            .where(
                aion_memory_records.c.memory_id == memory_id,
                aion_memory_records.c.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC))
        )
        with self._engine.begin() as connection:
            result = connection.execute(statement)
        return result.rowcount == 1

    def update_metadata(self, memory_id: str, metadata: dict[str, Any]) -> MemoryRecord | None:
        """Update public metadata for an active memory record."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                update(aion_memory_records)
                .where(
                    aion_memory_records.c.memory_id == memory_id,
                    aion_memory_records.c.deleted_at.is_(None),
                )
                .values(metadata=metadata)
            )
        return self.get(memory_id)

    def expire(self, memory_id: str, expires_at: datetime | None = None) -> bool:
        """Set a memory expiration timestamp without deleting it."""
        self._ensure_schema()
        statement = (
            update(aion_memory_records)
            .where(
                aion_memory_records.c.memory_id == memory_id,
                aion_memory_records.c.deleted_at.is_(None),
            )
            .values(expires_at=expires_at or datetime.now(UTC))
        )
        with self._engine.begin() as connection:
            result = connection.execute(statement)
        return result.rowcount == 1

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return

        memory_metadata.create_all(self._engine)
        self._schema_ready = True

    def _row_to_record(self, row: RowMapping) -> MemoryRecord:
        return MemoryRecord(
            memory_id=str(row["memory_id"]),
            memory_type=_memory_type(row["memory_type"]),
            owner_scope=list(row["owner_scope"]),
            source_event_id=_optional_str(row["source_event_id"]),
            content_ref=_optional_str(row["content_ref"]),
            summary=str(row["summary"]),
            confidence=float(row["confidence"]),
            sensitivity=str(row["sensitivity"]),
            created_at=_coerce_datetime(row["created_at"]),
            expires_at=_optional_datetime(row["expires_at"]),
            metadata=dict(row["metadata"]),
        )


def _scope_matches(record_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(record_scope).intersection(requested_scope))


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    return _coerce_datetime(value)


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")


def _memory_type(value: Any) -> MemoryType:
    allowed = {
        "working",
        "episodic",
        "semantic",
        "procedural",
        "preference",
        "graph",
        "audit",
    }
    if value not in allowed:
        raise ValueError(f"Unknown memory type: {value}")
    return cast(MemoryType, value)


def _is_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return False
    return expires_at <= datetime.now(UTC)
