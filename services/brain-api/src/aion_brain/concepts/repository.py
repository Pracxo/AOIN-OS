"""Persistence for the AION concept registry."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
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

from aion_brain.contracts.concepts import ConceptRecord

concept_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_concepts = Table(
    "aion_concepts",
    concept_metadata,
    Column("concept_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("name", Text, nullable=False),
    Column("normalized_name", Text, nullable=False),
    Column("concept_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("aliases", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_concepts_normalized_name", "normalized_name"),
    Index("ix_aion_concepts_concept_type", "concept_type"),
    Index("ix_aion_concepts_status", "status"),
    Index("ix_aion_concepts_created_at", "created_at"),
    Index("ix_aion_concepts_archived_at", "archived_at"),
)


class ConceptRepository:
    """Repository for concept records."""

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

    def save(self, concept: ConceptRecord) -> ConceptRecord:
        """Insert or update one concept."""
        self._ensure_schema()
        values = concept.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_concepts.c.concept_id).where(
                    aion_concepts.c.concept_id == concept.concept_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_concepts).values(**values))
            else:
                connection.execute(
                    update(aion_concepts)
                    .where(aion_concepts.c.concept_id == concept.concept_id)
                    .values(**values)
                )
        return concept

    def get(self, concept_id: str) -> ConceptRecord | None:
        """Return one concept by id."""
        self._ensure_schema()
        row = self._first(select(aion_concepts).where(aion_concepts.c.concept_id == concept_id))
        return _row_to_concept(row) if row is not None else None

    def find_by_normalized_name(
        self,
        normalized_name: str,
        scope: list[str],
    ) -> ConceptRecord | None:
        """Return an active concept with a matching normalized name and scope."""
        self._ensure_schema()
        rows = self._all(
            select(aion_concepts).where(
                aion_concepts.c.normalized_name == normalized_name,
                aion_concepts.c.status == "active",
            )
        )
        for row in rows:
            concept = _row_to_concept(row)
            if _scope_matches(concept.owner_scope, scope):
                return concept
        return None

    def list_concepts(
        self,
        *,
        scope: list[str],
        query: str | None = None,
        concept_types: list[str] | None = None,
        status: str | None = "active",
        limit: int = 100,
    ) -> list[ConceptRecord]:
        """List concepts visible to scope."""
        self._ensure_schema()
        statement = select(aion_concepts).order_by(aion_concepts.c.created_at.desc())
        if status is not None:
            statement = statement.where(aion_concepts.c.status == status)
        if concept_types:
            statement = statement.where(aion_concepts.c.concept_type.in_(concept_types))
        rows = self._all(statement)
        needle = query.lower() if query else None
        concepts: list[ConceptRecord] = []
        for row in rows:
            concept = _row_to_concept(row)
            if not _scope_matches(concept.owner_scope, scope):
                continue
            if (
                needle
                and needle not in concept.normalized_name
                and needle not in concept.name.lower()
            ):
                continue
            concepts.append(concept)
            if len(concepts) >= limit:
                break
        return concepts

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        if self._auto_create:
            concept_metadata.create_all(self._engine)
        self._schema_ready = True

    def _first(self, statement: Any) -> RowMapping | None:
        with self._engine.begin() as connection:
            row = connection.execute(statement).mappings().first()
        return row

    def _all(self, statement: Any) -> list[RowMapping]:
        with self._engine.begin() as connection:
            rows = list(connection.execute(statement).mappings().all())
        return rows


def _row_to_concept(row: RowMapping) -> ConceptRecord:
    return ConceptRecord(**dict(row))


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(set(requested_scope)))


def now_utc() -> datetime:
    """Return current UTC time for repository-adjacent callers."""
    return datetime.now(UTC)
