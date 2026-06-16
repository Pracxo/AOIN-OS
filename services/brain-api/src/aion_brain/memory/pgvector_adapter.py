"""pgvector semantic memory adapter boundary."""

import hashlib
import re
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.memory import (
    MemoryRecord,
    MemoryType,
    SemanticIndexResponse,
    SemanticMemoryQuery,
    SemanticMemoryResult,
    TurboVecIndexStatus,
    TurboVecRebuildRequest,
    TurboVecRebuildResponse,
)
from aion_brain.embeddings.base import EmbeddingAdapter
from aion_brain.embeddings.hash_embedding import HashEmbeddingAdapter
from aion_brain.memory.repository import MemoryRepository, memory_metadata


class PgVectorSemanticMemoryAdapter:
    """Adapter boundary for pgvector semantic recall."""

    adapter_name = "pgvector"

    def __init__(
        self,
        *,
        memory_repository: MemoryRepository,
        database_url: str | None = None,
        engine: Engine | None = None,
        embedding_adapter: EmbeddingAdapter | None = None,
        dimensions: int = 384,
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
        self._memory_repository = memory_repository
        self._embedding_adapter = embedding_adapter or HashEmbeddingAdapter(dimensions)
        self._dimensions = dimensions
        self._auto_create = auto_create
        self._schema_ready = False

    def remember(self, record: MemoryRecord) -> str:
        """Index a canonical memory record summary in pgvector."""
        if self._memory_repository.get(record.memory_id) is None:
            raise ValueError(f"canonical memory record not found: {record.memory_id}")
        self._ensure_schema()
        embedding_id = _embedding_id(record.memory_id, self.adapter_name)
        values = {
            "embedding_id": embedding_id,
            "memory_id": record.memory_id,
            "adapter_name": self.adapter_name,
            "embedding_model": self._embedding_adapter.model_name(),
            "dimensions": self._embedding_adapter.dimensions(),
            "embedding": _vector_literal(self._embedding_adapter.embed_text(record.summary)),
            "source_text_hash": _source_text_hash(record.summary),
            "updated_at": datetime.now(UTC),
        }
        statement = text(
            """
            INSERT INTO aion_semantic_embeddings (
                embedding_id,
                memory_id,
                adapter_name,
                embedding_model,
                dimensions,
                embedding,
                source_text_hash,
                updated_at
            )
            VALUES (
                :embedding_id,
                :memory_id,
                :adapter_name,
                :embedding_model,
                :dimensions,
                CAST(:embedding AS vector),
                :source_text_hash,
                :updated_at
            )
            ON CONFLICT (embedding_id) DO UPDATE SET
                adapter_name = EXCLUDED.adapter_name,
                embedding_model = EXCLUDED.embedding_model,
                dimensions = EXCLUDED.dimensions,
                embedding = EXCLUDED.embedding,
                source_text_hash = EXCLUDED.source_text_hash,
                updated_at = EXCLUDED.updated_at,
                deleted_at = NULL
            """
        )
        with self._engine.begin() as connection:
            connection.execute(statement, values)
        return embedding_id

    def retrieve(self, query: SemanticMemoryQuery) -> list[SemanticMemoryResult]:
        """Retrieve memories using pgvector cosine similarity."""
        self._ensure_schema()
        query_embedding = _vector_literal(self._embedding_adapter.embed_text(query.query))
        candidate_limit = max(query.limit * 5, 100)
        statement = text(
            """
            SELECT
                m.memory_id,
                m.memory_type,
                m.owner_scope,
                m.source_event_id,
                m.content_ref,
                m.summary,
                m.confidence,
                m.sensitivity,
                m.created_at,
                m.expires_at,
                m.metadata,
                e.embedding_id,
                e.embedding_model,
                e.source_text_hash,
                1 - (e.embedding <=> CAST(:query_embedding AS vector)) AS score
            FROM aion_semantic_embeddings e
            JOIN aion_memory_records m ON m.memory_id = e.memory_id
            WHERE e.deleted_at IS NULL
              AND m.deleted_at IS NULL
              AND e.adapter_name = :adapter_name
              AND e.dimensions = :dimensions
            ORDER BY e.embedding <=> CAST(:query_embedding AS vector)
            LIMIT :candidate_limit
            """
        )
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    statement,
                    {
                        "query_embedding": query_embedding,
                        "adapter_name": self.adapter_name,
                        "dimensions": self._embedding_adapter.dimensions(),
                        "candidate_limit": candidate_limit,
                    },
                )
                .mappings()
                .all()
            )
        results = [
            _result_from_row(row, query, self.adapter_name)
            for row in rows
            if _row_matches(row, query)
        ]
        filtered = [
            result
            for result in results
            if query.min_score is None or result.score >= query.min_score
        ]
        return filtered[: query.limit]

    def forget(self, memory_id: str) -> bool:
        """Soft-delete semantic vectors for a memory record."""
        self._ensure_schema()
        statement = text(
            """
            UPDATE aion_semantic_embeddings
            SET deleted_at = :deleted_at, updated_at = :deleted_at
            WHERE memory_id = :memory_id
              AND adapter_name = :adapter_name
              AND deleted_at IS NULL
            """
        )
        with self._engine.begin() as connection:
            result = connection.execute(
                statement,
                {
                    "deleted_at": datetime.now(UTC),
                    "memory_id": memory_id,
                    "adapter_name": self.adapter_name,
                },
            )
        return result.rowcount > 0

    def reindex(self, memory_id: str) -> SemanticIndexResponse:
        """Recompute a semantic embedding from the latest memory summary."""
        record = self._memory_repository.get(memory_id)
        if record is None:
            return SemanticIndexResponse(
                indexed=False,
                memory_id=memory_id,
                adapter_name=self.adapter_name,
                embedding_id=None,
                reason="memory_not_found",
            )
        embedding_id = self.remember(record)
        return SemanticIndexResponse(
            indexed=True,
            memory_id=memory_id,
            adapter_name=self.adapter_name,
            embedding_id=embedding_id,
            reason=None,
        )

    def status(self, index_name: str = "default") -> TurboVecIndexStatus | None:
        """pgvector has no TurboVec index status."""
        return None

    def rebuild(self, request: TurboVecRebuildRequest) -> TurboVecRebuildResponse:
        """pgvector does not rebuild TurboVec indexes."""
        raise RuntimeError("turbovec_not_selected")

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        memory_metadata.create_all(self._engine)
        with self._engine.begin() as connection:
            if self._engine.dialect.name == "postgresql":
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                connection.execute(text(_create_table_sql(self._dimensions)))
                connection.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_aion_semantic_embeddings_memory_id "
                        "ON aion_semantic_embeddings (memory_id)"
                    )
                )
                connection.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_aion_semantic_embeddings_adapter_name "
                        "ON aion_semantic_embeddings (adapter_name)"
                    )
                )
                connection.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_aion_semantic_embeddings_dimensions "
                        "ON aion_semantic_embeddings (dimensions)"
                    )
                )
                connection.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_aion_semantic_embeddings_deleted_at "
                        "ON aion_semantic_embeddings (deleted_at)"
                    )
                )
                try:
                    connection.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS "
                            "ix_aion_semantic_embeddings_embedding_cosine "
                            "ON aion_semantic_embeddings USING ivfflat "
                            "(embedding vector_cosine_ops) WITH (lists = 100)"
                        )
                    )
                except Exception:
                    pass
        self._schema_ready = True


def _create_table_sql(dimensions: int) -> str:
    return f"""
    CREATE TABLE IF NOT EXISTS aion_semantic_embeddings (
        embedding_id TEXT PRIMARY KEY,
        memory_id TEXT NOT NULL,
        adapter_name TEXT NOT NULL,
        embedding_model TEXT NOT NULL,
        dimensions INTEGER NOT NULL,
        embedding VECTOR({dimensions}) NOT NULL,
        source_text_hash TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        deleted_at TIMESTAMPTZ NULL
    )
    """


def _row_matches(row: RowMapping, query: SemanticMemoryQuery) -> bool:
    if not _scope_matches(list(row["owner_scope"]), query.scope):
        return False
    allowed_types = set(query.memory_types)
    return not allowed_types or row["memory_type"] in allowed_types


def _result_from_row(
    row: RowMapping,
    query: SemanticMemoryQuery,
    adapter_name: str,
) -> SemanticMemoryResult:
    record = _row_to_record(row)
    score = max(0.0, min(1.0, float(row["score"])))
    return SemanticMemoryResult(
        memory=record,
        score=score,
        retrieval_source="semantic",
        adapter_name=adapter_name,
        matched_terms=sorted(_tokens(query.query).intersection(_tokens(record.summary))),
        metadata={
            "embedding_id": str(row["embedding_id"]),
            "embedding_model": str(row["embedding_model"]),
            "source_text_hash": str(row["source_text_hash"]),
        },
    )


def result_from_memory_for_unit(
    record: MemoryRecord,
    *,
    score: float,
    query: str,
    adapter_name: str = "pgvector",
) -> SemanticMemoryResult:
    """Build a semantic result contract without exposing pgvector internals."""
    return SemanticMemoryResult(
        memory=record,
        score=max(0.0, min(1.0, score)),
        retrieval_source="semantic",
        adapter_name=adapter_name,
        matched_terms=sorted(_tokens(query).intersection(_tokens(record.summary))),
        metadata={},
    )


def _row_to_record(row: RowMapping) -> MemoryRecord:
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


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _embedding_id(memory_id: str, adapter_name: str) -> str:
    return f"{adapter_name}-{memory_id}"


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.12f}" for value in vector) + "]"


def _source_text_hash(text_value: str) -> str:
    return hashlib.sha256(text_value.encode("utf-8")).hexdigest()


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
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed
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
