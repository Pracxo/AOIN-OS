"""Persistent retrieval trace repository."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Index,
    Integer,
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

from aion_brain.contracts.retrieval import RetrievalResult

retrieval_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_context_retrievals = Table(
    "aion_context_retrievals",
    retrieval_metadata,
    Column("retrieval_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("intent_id", Text, nullable=True),
    Column("context_id", Text, nullable=True),
    Column("query", Text, nullable=False),
    Column("scope", json_payload_type, nullable=False),
    Column("requested_sources", json_payload_type, nullable=False),
    Column("result_count", Integer, nullable=False),
    Column("results", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_context_retrievals_trace_id", "trace_id"),
    Index("ix_aion_context_retrievals_intent_id", "intent_id"),
    Index("ix_aion_context_retrievals_context_id", "context_id"),
    Index("ix_aion_context_retrievals_created_at", "created_at"),
)


class RetrievalRepository:
    """Repository for retrieval traces."""

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

    def save(
        self,
        result: RetrievalResult,
        *,
        trace_id: str | None,
        intent_id: str | None,
        context_id: str | None,
        scope: list[str],
        requested_sources: list[str],
    ) -> RetrievalResult:
        """Persist a retrieval result."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_context_retrievals).values(
                    retrieval_id=result.retrieval_id,
                    trace_id=trace_id,
                    intent_id=intent_id,
                    context_id=context_id,
                    query=result.query,
                    scope=scope,
                    requested_sources=requested_sources,
                    result_count=len(result.items),
                    results=result.model_dump(mode="json"),
                    created_at=result.created_at,
                )
            )
        return result

    def get(self, retrieval_id: str) -> RetrievalResult | None:
        """Return a persisted retrieval result."""
        self._ensure_schema()
        statement = select(aion_context_retrievals).where(
            aion_context_retrievals.c.retrieval_id == retrieval_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        return _row_to_result(row)

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        retrieval_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_result(row: RowMapping) -> RetrievalResult:
    payload = dict(row["results"])
    return RetrievalResult.model_validate(payload)


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")
