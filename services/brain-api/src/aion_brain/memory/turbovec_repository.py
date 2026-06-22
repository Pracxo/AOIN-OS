"""TurboVec index metadata repository."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, TypedDict, cast

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
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

from aion_brain.contracts.memory import TurboVecIndexStatus

turbovec_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_turbovec_indexes = Table(
    "aion_turbovec_indexes",
    turbovec_metadata,
    Column("index_id", Text, primary_key=True),
    Column("index_name", Text, nullable=False),
    Column("adapter_name", Text, nullable=False),
    Column("dimensions", Integer, nullable=False),
    Column("bit_width", Integer, nullable=False),
    Column("index_path", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("rebuilt_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_turbovec_indexes_index_name", "index_name"),
    Index("ix_aion_turbovec_indexes_adapter_name", "adapter_name"),
    Index("ix_aion_turbovec_indexes_status", "status"),
    Index("ix_aion_turbovec_indexes_dimensions", "dimensions"),
    Index("ix_aion_turbovec_indexes_bit_width", "bit_width"),
    Index("ix_aion_turbovec_indexes_created_at", "created_at"),
)

aion_turbovec_index_entries = Table(
    "aion_turbovec_index_entries",
    turbovec_metadata,
    Column("entry_id", Text, primary_key=True),
    Column(
        "index_id",
        Text,
        ForeignKey("aion_turbovec_indexes.index_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("memory_id", Text, nullable=False),
    Column("vector_id", BigInteger, nullable=False),
    Column("source_text_hash", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("memory_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("index_id", "memory_id", name="uq_aion_turbovec_entry_memory"),
    UniqueConstraint("index_id", "vector_id", name="uq_aion_turbovec_entry_vector"),
    Index("ix_aion_turbovec_index_entries_index_id", "index_id"),
    Index("ix_aion_turbovec_index_entries_memory_id", "memory_id"),
    Index("ix_aion_turbovec_index_entries_vector_id", "vector_id"),
    Index("ix_aion_turbovec_index_entries_source_text_hash", "source_text_hash"),
    Index("ix_aion_turbovec_index_entries_memory_type", "memory_type"),
    Index("ix_aion_turbovec_index_entries_status", "status"),
    Index("ix_aion_turbovec_index_entries_deleted_at", "deleted_at"),
)


class TurboVecEntry(TypedDict):
    """Plain typed dict for TurboVec index entry metadata."""

    entry_id: str
    index_id: str
    memory_id: str
    vector_id: int
    source_text_hash: str
    owner_scope: list[str]
    memory_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class TurboVecRepository:
    """Persistence boundary for TurboVec index metadata."""

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

    def create_or_get_index(
        self,
        index_name: str,
        dimensions: int,
        bit_width: int,
        index_path: str,
    ) -> TurboVecIndexStatus:
        """Create or return an index metadata record."""
        existing = self.get_index(index_name)
        if existing is not None:
            return existing
        now = datetime.now(UTC)
        status = TurboVecIndexStatus(
            index_id=f"turbovec-{index_name}",
            index_name=index_name,
            adapter_name="turbovec",
            dimensions=dimensions,
            bit_width=bit_width,
            index_path=index_path,
            status="active",
            entry_count=0,
            available=True,
            reason=None,
            metadata={},
            created_at=now,
            updated_at=now,
            rebuilt_at=None,
        )
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(insert(aion_turbovec_indexes).values(**_status_values(status)))
        return status

    def get_index(self, index_name: str) -> TurboVecIndexStatus | None:
        """Return index metadata by name."""
        self._ensure_schema()
        statement = select(aion_turbovec_indexes).where(
            aion_turbovec_indexes.c.index_name == index_name
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return self._status_from_row(row) if row is not None else None

    def update_index_status(
        self,
        index_id: str,
        status: str,
        reason: str | None = None,
    ) -> TurboVecIndexStatus:
        """Update index state and return the latest status."""
        self._ensure_schema()
        existing = self._get_index_by_id(index_id)
        if existing is None:
            raise KeyError(index_id)
        metadata = dict(existing.metadata)
        if reason is not None:
            metadata["reason"] = reason
        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            connection.execute(
                update(aion_turbovec_indexes)
                .where(aion_turbovec_indexes.c.index_id == index_id)
                .values(status=status, metadata=metadata, updated_at=now)
            )
        updated = self._get_index_by_id(index_id)
        if updated is None:
            raise KeyError(index_id)
        return updated

    def mark_rebuilt(self, index_id: str) -> TurboVecIndexStatus:
        """Mark an index as rebuilt now."""
        self._ensure_schema()
        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            connection.execute(
                update(aion_turbovec_indexes)
                .where(aion_turbovec_indexes.c.index_id == index_id)
                .values(status="active", updated_at=now, rebuilt_at=now)
            )
        updated = self._get_index_by_id(index_id)
        if updated is None:
            raise KeyError(index_id)
        return updated

    def upsert_entry(
        self,
        index_id: str,
        memory_id: str,
        vector_id: int,
        source_text_hash: str,
        owner_scope: list[str],
        memory_type: str,
    ) -> None:
        """Upsert a vector-to-memory metadata mapping."""
        self._ensure_schema()
        now = datetime.now(UTC)
        existing = self.get_entry_by_memory(index_id, memory_id)
        values = {
            "entry_id": existing["entry_id"] if existing else f"{index_id}-{memory_id}",
            "index_id": index_id,
            "memory_id": memory_id,
            "vector_id": vector_id,
            "source_text_hash": source_text_hash,
            "owner_scope": owner_scope,
            "memory_type": memory_type,
            "status": "active",
            "created_at": existing["created_at"] if existing else now,
            "updated_at": now,
            "deleted_at": None,
        }
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_turbovec_index_entries).where(
                    aion_turbovec_index_entries.c.index_id == index_id,
                    aion_turbovec_index_entries.c.memory_id == memory_id,
                )
            )
            connection.execute(insert(aion_turbovec_index_entries).values(**values))

    def get_entry_by_memory(self, index_id: str, memory_id: str) -> TurboVecEntry | None:
        """Return entry metadata by memory ID."""
        self._ensure_schema()
        statement = select(aion_turbovec_index_entries).where(
            aion_turbovec_index_entries.c.index_id == index_id,
            aion_turbovec_index_entries.c.memory_id == memory_id,
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _entry_from_row(row) if row is not None else None

    def get_entry_by_vector(self, index_id: str, vector_id: int) -> TurboVecEntry | None:
        """Return entry metadata by vector ID."""
        self._ensure_schema()
        statement = select(aion_turbovec_index_entries).where(
            aion_turbovec_index_entries.c.index_id == index_id,
            aion_turbovec_index_entries.c.vector_id == vector_id,
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _entry_from_row(row) if row is not None else None

    def list_active_entries(
        self,
        index_id: str,
        scope: list[str],
        memory_types: list[str] | None = None,
        limit: int = 10000,
    ) -> list[TurboVecEntry]:
        """List active entries within scope."""
        self._ensure_schema()
        statement = select(aion_turbovec_index_entries).where(
            aion_turbovec_index_entries.c.index_id == index_id,
            aion_turbovec_index_entries.c.status == "active",
            aion_turbovec_index_entries.c.deleted_at.is_(None),
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        allowed_types = set(memory_types or [])
        entries = [
            _entry_from_row(row)
            for row in rows
            if _scope_matches(list(row["owner_scope"]), scope)
            and (not allowed_types or row["memory_type"] in allowed_types)
        ]
        return entries[:limit]

    def soft_delete_entry(self, index_id: str, memory_id: str) -> bool:
        """Soft-delete an index entry."""
        self._ensure_schema()
        deleted_at = datetime.now(UTC)
        with self._engine.begin() as connection:
            result = connection.execute(
                update(aion_turbovec_index_entries)
                .where(
                    aion_turbovec_index_entries.c.index_id == index_id,
                    aion_turbovec_index_entries.c.memory_id == memory_id,
                    aion_turbovec_index_entries.c.deleted_at.is_(None),
                )
                .values(status="deleted", deleted_at=deleted_at, updated_at=deleted_at)
            )
        return result.rowcount > 0

    def count_entries(self, index_id: str) -> int:
        """Count active entries for an index."""
        return len(self.list_active_entries(index_id, scope=["*"], limit=1_000_000))

    def _status_from_row(self, row: RowMapping) -> TurboVecIndexStatus:
        entry_count = len(
            [
                entry
                for entry in self.list_active_entries(
                    str(row["index_id"]),
                    scope=["*"],
                    limit=1_000_000,
                )
                if entry["status"] == "active"
            ]
        )
        metadata = dict(row["metadata"])
        return TurboVecIndexStatus(
            index_id=str(row["index_id"]),
            index_name=str(row["index_name"]),
            adapter_name=str(row["adapter_name"]),
            dimensions=int(row["dimensions"]),
            bit_width=int(row["bit_width"]),
            index_path=str(row["index_path"]),
            status=cast(Any, row["status"]),
            entry_count=entry_count,
            available=str(row["status"]) == "active",
            reason=cast(str | None, metadata.get("reason")),
            metadata=metadata,
            created_at=_coerce_datetime(row["created_at"]),
            updated_at=_coerce_datetime(row["updated_at"]),
            rebuilt_at=_optional_datetime(row["rebuilt_at"]),
        )

    def _get_index_by_id(self, index_id: str) -> TurboVecIndexStatus | None:
        self._ensure_schema()
        statement = select(aion_turbovec_indexes).where(
            aion_turbovec_indexes.c.index_id == index_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return self._status_from_row(row) if row is not None else None

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        turbovec_metadata.create_all(self._engine)
        self._schema_ready = True


def _status_values(status: TurboVecIndexStatus) -> dict[str, Any]:
    values = status.model_dump(mode="python")
    values.pop("entry_count")
    values.pop("available")
    values.pop("reason")
    if status.reason is not None:
        values["metadata"] = {**status.metadata, "reason": status.reason}
    return values


def _entry_from_row(row: RowMapping) -> TurboVecEntry:
    return {
        "entry_id": str(row["entry_id"]),
        "index_id": str(row["index_id"]),
        "memory_id": str(row["memory_id"]),
        "vector_id": int(row["vector_id"]),
        "source_text_hash": str(row["source_text_hash"]),
        "owner_scope": list(row["owner_scope"]),
        "memory_type": str(row["memory_type"]),
        "status": str(row["status"]),
        "created_at": _coerce_datetime(row["created_at"]),
        "updated_at": _coerce_datetime(row["updated_at"]),
        "deleted_at": _optional_datetime(row["deleted_at"]),
    }


def _scope_matches(record_scope: list[str], requested_scope: list[str]) -> bool:
    return "*" in requested_scope or bool(set(record_scope).intersection(requested_scope))


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    return _coerce_datetime(value)


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")
