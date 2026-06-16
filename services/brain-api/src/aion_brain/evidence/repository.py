"""Persistent Evidence Vault repository."""

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

from aion_brain.contracts.evidence import (
    EvidenceChunk,
    EvidenceLink,
    EvidenceRecord,
    EvidenceRelationType,
    EvidenceSourceType,
    EvidenceTargetType,
    GroundingClaim,
    GroundingVerificationStatus,
)

evidence_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_evidence_records = Table(
    "aion_evidence_records",
    evidence_metadata,
    Column("evidence_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_ref", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text, nullable=False),
    Column("content_hash", Text, nullable=False),
    Column("content_ref", Text, nullable=True),
    Column("media_type", Text, nullable=False),
    Column("sensitivity", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_evidence_records_trace_id", "trace_id"),
    Index("ix_aion_evidence_records_source_type", "source_type"),
    Index("ix_aion_evidence_records_content_hash", "content_hash"),
    Index("ix_aion_evidence_records_sensitivity", "sensitivity"),
    Index("ix_aion_evidence_records_created_at", "created_at"),
    Index("ix_aion_evidence_records_deleted_at", "deleted_at"),
)

aion_evidence_chunks = Table(
    "aion_evidence_chunks",
    evidence_metadata,
    Column("chunk_id", Text, primary_key=True),
    Column(
        "evidence_id",
        Text,
        ForeignKey("aion_evidence_records.evidence_id"),
        nullable=False,
    ),
    Column("chunk_index", Integer, nullable=False),
    Column("text", Text, nullable=False),
    Column("text_hash", Text, nullable=False),
    Column("token_count_hint", Integer, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_evidence_chunks_evidence_id", "evidence_id"),
    Index("ix_aion_evidence_chunks_chunk_index", "chunk_index"),
    Index("ix_aion_evidence_chunks_text_hash", "text_hash"),
    Index("ix_aion_evidence_chunks_deleted_at", "deleted_at"),
)

aion_evidence_links = Table(
    "aion_evidence_links",
    evidence_metadata,
    Column("link_id", Text, primary_key=True),
    Column(
        "evidence_id",
        Text,
        ForeignKey("aion_evidence_records.evidence_id"),
        nullable=False,
    ),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column("relation_type", Text, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("confidence", Float, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_evidence_links_evidence_id", "evidence_id"),
    Index("ix_aion_evidence_links_target_type", "target_type"),
    Index("ix_aion_evidence_links_target_id", "target_id"),
    Index("ix_aion_evidence_links_relation_type", "relation_type"),
    Index("ix_aion_evidence_links_trace_id", "trace_id"),
    Index("ix_aion_evidence_links_deleted_at", "deleted_at"),
)

aion_grounding_claims = Table(
    "aion_grounding_claims",
    evidence_metadata,
    Column("claim_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("statement", Text, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("chunk_refs", json_payload_type, nullable=False),
    Column("score", Float, nullable=False),
    Column("verification_status", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_grounding_claims_trace_id", "trace_id"),
    Index("ix_aion_grounding_claims_verification_status", "verification_status"),
    Index("ix_aion_grounding_claims_score", "score"),
    Index("ix_aion_grounding_claims_created_at", "created_at"),
)


class EvidenceRepository:
    """Repository for evidence, chunks, links, and grounding claims."""

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
            self._engine = create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_evidence(self, record: EvidenceRecord) -> EvidenceRecord:
        """Persist evidence metadata."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = record.model_copy(
            update={
                "created_at": record.created_at or now,
                "updated_at": now,
                "deleted_at": record.deleted_at,
            }
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_evidence_records).values(**stored.model_dump(mode="python"))
            )
        return stored

    def save_chunks(self, chunks: list[EvidenceChunk]) -> list[EvidenceChunk]:
        """Persist evidence chunks."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = [
            chunk.model_copy(update={"created_at": chunk.created_at or now}) for chunk in chunks
        ]
        if stored:
            with self._engine.begin() as connection:
                connection.execute(
                    insert(aion_evidence_chunks),
                    [chunk.model_dump(mode="python") for chunk in stored],
                )
        return stored

    def get_evidence(self, evidence_id: str) -> EvidenceRecord | None:
        """Return active evidence by ID."""
        self._ensure_schema()
        statement = select(aion_evidence_records).where(
            aion_evidence_records.c.evidence_id == evidence_id,
            aion_evidence_records.c.deleted_at.is_(None),
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_evidence(row) if row is not None else None

    def list_evidence(
        self,
        scope: list[str],
        *,
        source_types: list[str] | None = None,
        limit: int = 500,
    ) -> list[EvidenceRecord]:
        """List active evidence within scope."""
        self._ensure_schema()
        statement = (
            select(aion_evidence_records)
            .where(aion_evidence_records.c.deleted_at.is_(None))
            .order_by(aion_evidence_records.c.created_at.desc())
            .limit(limit)
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        allowed = set(source_types or [])
        return [
            _row_to_evidence(row)
            for row in rows
            if _scope_matches(list(row["owner_scope"]), scope)
            and (not allowed or str(row["source_type"]) in allowed)
        ]

    def get_chunks(self, evidence_id: str) -> list[EvidenceChunk]:
        """Return active chunks for evidence."""
        self._ensure_schema()
        statement = (
            select(aion_evidence_chunks)
            .where(
                aion_evidence_chunks.c.evidence_id == evidence_id,
                aion_evidence_chunks.c.deleted_at.is_(None),
            )
            .order_by(aion_evidence_chunks.c.chunk_index.asc())
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_chunk(row) for row in rows]

    def save_link(self, link: EvidenceLink) -> EvidenceLink:
        """Persist an evidence link."""
        self._ensure_schema()
        stored = link.model_copy(update={"created_at": link.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_evidence_links).values(**stored.model_dump(mode="python"))
            )
        return stored

    def list_links(self, evidence_id: str) -> list[EvidenceLink]:
        """Return active links for evidence."""
        self._ensure_schema()
        statement = (
            select(aion_evidence_links)
            .where(
                aion_evidence_links.c.evidence_id == evidence_id,
                aion_evidence_links.c.deleted_at.is_(None),
            )
            .order_by(aion_evidence_links.c.created_at.desc())
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_link(row) for row in rows]

    def list_links_for_evidence_ids(
        self,
        evidence_ids: list[str],
        *,
        relation_type: str | None = None,
    ) -> list[EvidenceLink]:
        """Return links for selected evidence IDs."""
        if not evidence_ids:
            return []
        self._ensure_schema()
        statement = select(aion_evidence_links).where(
            aion_evidence_links.c.evidence_id.in_(evidence_ids),
            aion_evidence_links.c.deleted_at.is_(None),
        )
        if relation_type is not None:
            statement = statement.where(aion_evidence_links.c.relation_type == relation_type)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_link(row) for row in rows]

    def save_grounding_claim(self, claim: GroundingClaim) -> GroundingClaim:
        """Persist a grounding claim."""
        self._ensure_schema()
        stored = claim.model_copy(update={"created_at": claim.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_grounding_claims).values(**stored.model_dump(mode="python"))
            )
        return stored

    def soft_delete_evidence(self, evidence_id: str) -> bool:
        """Soft-delete evidence and its dependent chunks and links."""
        self._ensure_schema()
        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            result = connection.execute(
                update(aion_evidence_records)
                .where(
                    aion_evidence_records.c.evidence_id == evidence_id,
                    aion_evidence_records.c.deleted_at.is_(None),
                )
                .values(deleted_at=now, updated_at=now)
            )
            connection.execute(
                update(aion_evidence_chunks)
                .where(
                    aion_evidence_chunks.c.evidence_id == evidence_id,
                    aion_evidence_chunks.c.deleted_at.is_(None),
                )
                .values(deleted_at=now)
            )
            connection.execute(
                update(aion_evidence_links)
                .where(
                    aion_evidence_links.c.evidence_id == evidence_id,
                    aion_evidence_links.c.deleted_at.is_(None),
                )
                .values(deleted_at=now)
            )
        return result.rowcount == 1

    def soft_delete_link(self, link_id: str) -> bool:
        """Soft-delete one evidence link without deleting source evidence."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            result = connection.execute(
                update(aion_evidence_links)
                .where(
                    aion_evidence_links.c.link_id == link_id,
                    aion_evidence_links.c.deleted_at.is_(None),
                )
                .values(deleted_at=datetime.now(UTC))
            )
        return result.rowcount == 1

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        evidence_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_evidence(row: RowMapping) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=str(row["evidence_id"]),
        trace_id=_optional_str(row["trace_id"]),
        source_type=cast(EvidenceSourceType, str(row["source_type"])),
        source_ref=_optional_str(row["source_ref"]),
        owner_scope=list(row["owner_scope"]),
        title=str(row["title"]),
        summary=str(row["summary"]),
        content_hash=str(row["content_hash"]),
        content_ref=_optional_str(row["content_ref"]),
        media_type=str(row["media_type"]),
        sensitivity=cast(Any, str(row["sensitivity"])),
        confidence=float(row["confidence"]),
        metadata=dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        deleted_at=_optional_datetime(row["deleted_at"]),
    )


def _row_to_chunk(row: RowMapping) -> EvidenceChunk:
    return EvidenceChunk(
        chunk_id=str(row["chunk_id"]),
        evidence_id=str(row["evidence_id"]),
        chunk_index=int(row["chunk_index"]),
        text=str(row["text"]),
        text_hash=str(row["text_hash"]),
        token_count_hint=int(row["token_count_hint"]),
        metadata=dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        deleted_at=_optional_datetime(row["deleted_at"]),
    )


def _row_to_link(row: RowMapping) -> EvidenceLink:
    return EvidenceLink(
        link_id=str(row["link_id"]),
        evidence_id=str(row["evidence_id"]),
        target_type=cast(EvidenceTargetType, str(row["target_type"])),
        target_id=str(row["target_id"]),
        relation_type=cast(EvidenceRelationType, str(row["relation_type"])),
        trace_id=_optional_str(row["trace_id"]),
        confidence=float(row["confidence"]),
        metadata=dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        deleted_at=_optional_datetime(row["deleted_at"]),
    )


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
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")


def _scope_matches(record_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(record_scope).intersection(requested_scope))


def _verification_status(value: Any) -> GroundingVerificationStatus:
    return cast(GroundingVerificationStatus, str(value))
