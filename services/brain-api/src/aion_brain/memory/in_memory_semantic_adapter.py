"""In-memory semantic memory adapter for tests and local units."""

import re
from datetime import UTC, datetime

from aion_brain.contracts.memory import (
    MemoryRecord,
    SemanticIndexResponse,
    SemanticMemoryQuery,
    SemanticMemoryResult,
    TurboVecIndexStatus,
    TurboVecRebuildRequest,
    TurboVecRebuildResponse,
)
from aion_brain.embeddings.base import EmbeddingAdapter
from aion_brain.embeddings.hash_embedding import HashEmbeddingAdapter


class InMemorySemanticMemoryAdapter:
    """Deterministic in-memory semantic recall adapter."""

    adapter_name = "in-memory"

    def __init__(self, embedding_adapter: EmbeddingAdapter | None = None) -> None:
        self._embedding_adapter = embedding_adapter or HashEmbeddingAdapter()
        self._records: dict[str, MemoryRecord] = {}
        self._vectors: dict[str, list[float]] = {}
        self._deleted_at: dict[str, datetime] = {}

    def remember(self, record: MemoryRecord) -> str:
        """Store and index a memory record."""
        self._records[record.memory_id] = record
        self._vectors[record.memory_id] = self._embedding_adapter.embed_text(record.summary)
        self._deleted_at.pop(record.memory_id, None)
        return _embedding_id(record.memory_id, self.adapter_name)

    def retrieve(self, query: SemanticMemoryQuery) -> list[SemanticMemoryResult]:
        """Retrieve memories by cosine similarity."""
        query_vector = self._embedding_adapter.embed_text(query.query)
        allowed_types = set(query.memory_types)
        results = []
        for record in self._records.values():
            if record.memory_id in self._deleted_at:
                continue
            if _is_expired(record.expires_at):
                continue
            if not _scope_matches(record.owner_scope, query.scope):
                continue
            if allowed_types and record.memory_type not in allowed_types:
                continue
            score = _cosine_similarity(query_vector, self._vectors.get(record.memory_id, []))
            if query.min_score is not None and score < query.min_score:
                continue
            results.append(_result(record, score, query.query, self.adapter_name))
        return sorted(results, key=lambda result: result.score, reverse=True)[: query.limit]

    def forget(self, memory_id: str) -> bool:
        """Soft-delete one semantic vector."""
        if memory_id not in self._records or memory_id in self._deleted_at:
            return False
        self._deleted_at[memory_id] = datetime.now(UTC)
        return True

    def update_metadata(self, memory_id: str, metadata: dict[str, object]) -> MemoryRecord | None:
        """Update metadata for a stored active memory."""
        record = self._records.get(memory_id)
        if record is None or memory_id in self._deleted_at or _is_expired(record.expires_at):
            return None
        updated = record.model_copy(update={"metadata": dict(metadata)})
        self._records[memory_id] = updated
        return updated

    def reindex(self, memory_id: str) -> SemanticIndexResponse:
        """Reindex a stored memory record."""
        record = self._records.get(memory_id)
        if record is None or memory_id in self._deleted_at:
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
        """In-memory semantic recall has no TurboVec index status."""
        return None

    def rebuild(self, request: TurboVecRebuildRequest) -> TurboVecRebuildResponse:
        """In-memory semantic recall does not rebuild TurboVec indexes."""
        raise RuntimeError("turbovec_not_selected")


def _result(
    record: MemoryRecord,
    score: float,
    query: str,
    adapter_name: str,
) -> SemanticMemoryResult:
    return SemanticMemoryResult(
        memory=record,
        score=max(0.0, min(1.0, score)),
        retrieval_source="semantic",
        adapter_name=adapter_name,
        matched_terms=sorted(_tokens(query).intersection(_tokens(record.summary))),
        metadata={"embedding_adapter": "hash"},
    )


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(
        left_value * right_value for left_value, right_value in zip(left, right, strict=True)
    )


def _scope_matches(record_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(record_scope).intersection(requested_scope))


def _is_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at <= datetime.now(UTC)


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _embedding_id(memory_id: str, adapter_name: str) -> str:
    return f"{adapter_name}-{memory_id}"
