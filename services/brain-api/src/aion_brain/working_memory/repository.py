"""Working memory persistence."""

from datetime import UTC, datetime
from typing import Any, cast

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
    delete,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.working_memory import (
    WorkingMemorySlot,
    WorkingMemorySlotType,
    WorkingMemorySourceType,
)

working_memory_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_working_memory_slots = Table(
    "aion_working_memory_slots",
    working_memory_metadata,
    Column("slot_id", Text, primary_key=True),
    Column("focus_session_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("slot_type", Text, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=True),
    Column("content", json_payload_type, nullable=False),
    Column("summary", Text, nullable=False),
    Column("priority", Float, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("ttl_seconds", Integer, nullable=True),
    Column("expires_at", DateTime(timezone=True), nullable=True),
    Column("pinned", Boolean, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_working_memory_slots_focus_session_id", "focus_session_id"),
    Index("ix_aion_working_memory_slots_trace_id", "trace_id"),
    Index("ix_aion_working_memory_slots_actor_id", "actor_id"),
    Index("ix_aion_working_memory_slots_workspace_id", "workspace_id"),
    Index("ix_aion_working_memory_slots_slot_type", "slot_type"),
    Index("ix_aion_working_memory_slots_source_type", "source_type"),
    Index("ix_aion_working_memory_slots_source_id", "source_id"),
    Index("ix_aion_working_memory_slots_priority", "priority"),
    Index("ix_aion_working_memory_slots_expires_at", "expires_at"),
    Index("ix_aion_working_memory_slots_pinned", "pinned"),
    Index("ix_aion_working_memory_slots_deleted_at", "deleted_at"),
    Index("ix_aion_working_memory_slots_created_at", "created_at"),
)


class WorkingMemoryRepository:
    """Repository for short-lived working memory slots."""

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

    def save(self, slot: WorkingMemorySlot) -> WorkingMemorySlot:
        """Upsert one working memory slot."""
        self._ensure_schema()
        now = _now()
        stored = slot.model_copy(
            update={
                "created_at": slot.created_at or now,
                "updated_at": now,
            }
        )
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_working_memory_slots).where(
                    aion_working_memory_slots.c.slot_id == stored.slot_id
                )
            )
            connection.execute(
                insert(aion_working_memory_slots).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get(self, slot_id: str) -> WorkingMemorySlot | None:
        """Return one working memory slot."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_working_memory_slots).where(
                    aion_working_memory_slots.c.slot_id == slot_id
                )
            ).mappings().first()
        return _slot_from_row(row) if row is not None else None

    def list_slots(
        self,
        *,
        scope: list[str],
        focus_session_id: str | None = None,
        slot_types: list[str] | None = None,
        source_types: list[str] | None = None,
        include_expired: bool = False,
        pinned_only: bool = False,
        limit: int = 25,
        now: datetime | None = None,
    ) -> list[WorkingMemorySlot]:
        """List non-deleted slots visible to a scope."""
        self._ensure_schema()
        statement = select(aion_working_memory_slots).where(
            aion_working_memory_slots.c.deleted_at.is_(None)
        )
        if focus_session_id is not None:
            statement = statement.where(
                aion_working_memory_slots.c.focus_session_id == focus_session_id
            )
        if slot_types:
            statement = statement.where(aion_working_memory_slots.c.slot_type.in_(slot_types))
        if source_types:
            statement = statement.where(aion_working_memory_slots.c.source_type.in_(source_types))
        if pinned_only:
            statement = statement.where(aion_working_memory_slots.c.pinned.is_(True))
        statement = statement.order_by(
            aion_working_memory_slots.c.priority.desc(),
            aion_working_memory_slots.c.created_at.desc(),
        ).limit(limit * 4)
        cutoff = now or _now()
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        slots = [_slot_from_row(row) for row in rows]
        filtered = [
            slot
            for slot in slots
            if _scope_matches(slot.owner_scope, scope)
            and (include_expired or not _is_expired(slot, cutoff))
        ]
        return filtered[:limit]

    def sweep_expired(self, *, scope: list[str], limit: int = 100) -> list[WorkingMemorySlot]:
        """Soft-delete expired unpinned slots."""
        slots = self.list_slots(
            scope=scope,
            include_expired=True,
            pinned_only=False,
            limit=limit,
            now=_now(),
        )
        expired = [slot for slot in slots if _is_expired(slot, _now()) and not slot.pinned]
        for slot in expired[:limit]:
            self.save(slot.model_copy(update={"deleted_at": _now()}))
        return expired[:limit]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        working_memory_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _slot_from_row(row: RowMapping) -> WorkingMemorySlot:
    return WorkingMemorySlot(
        slot_id=str(row["slot_id"]),
        focus_session_id=_optional_str(row["focus_session_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        slot_type=cast(WorkingMemorySlotType, str(row["slot_type"])),
        source_type=cast(WorkingMemorySourceType, str(row["source_type"])),
        source_id=_optional_str(row["source_id"]),
        content=_dict(row["content"]),
        summary=str(row["summary"]),
        priority=float(row["priority"]),
        confidence=float(row["confidence"]),
        ttl_seconds=int(row["ttl_seconds"]) if row["ttl_seconds"] is not None else None,
        expires_at=_optional_datetime(row["expires_at"]),
        pinned=bool(row["pinned"]),
        owner_scope=_list_str(row["owner_scope"]),
        metadata=_dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        deleted_at=_optional_datetime(row["deleted_at"]),
    )


def _is_expired(slot: WorkingMemorySlot, now: datetime) -> bool:
    if slot.pinned or slot.expires_at is None:
        return False
    expires_at = (
        slot.expires_at
        if slot.expires_at.tzinfo is not None
        else slot.expires_at.replace(tzinfo=UTC)
    )
    return expires_at <= now


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_str(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _optional_str(value: Any) -> str | None:
    return str(value) if value is not None else None


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    return None


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope) & set(requested_scope))


def _now() -> datetime:
    return datetime.now(UTC)
