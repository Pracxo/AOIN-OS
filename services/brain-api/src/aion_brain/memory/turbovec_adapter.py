"""Optional TurboVec compressed semantic memory adapter."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from aion_brain.contracts.memory import (
    MemoryRecord,
    SemanticIndexResponse,
    SemanticMemoryQuery,
    SemanticMemoryResult,
    TurboVecIndexStatus,
    TurboVecRebuildRequest,
    TurboVecRebuildResponse,
)
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.embeddings.base import EmbeddingAdapter
from aion_brain.embeddings.hash_embedding import HashEmbeddingAdapter
from aion_brain.memory.repository import MemoryRepository
from aion_brain.memory.turbovec_compat import TurboVecCompat
from aion_brain.memory.turbovec_repository import TurboVecEntry, TurboVecRepository


class TurboVecSemanticMemoryAdapter:
    """Compressed semantic recall adapter behind AION's SemanticMemoryAdapter."""

    adapter_name = "turbovec"

    def __init__(
        self,
        *,
        memory_repository: MemoryRepository | None = None,
        turbovec_repository: TurboVecRepository | None = None,
        embedding_adapter: EmbeddingAdapter | None = None,
        telemetry_service: object | None = None,
        compat: TurboVecCompat | None = None,
        enabled: bool = False,
        index_name: str = "default",
        index_dir: str = "./.aion_indexes/turbovec",
        dimensions: int = 384,
        bit_width: int = 4,
        auto_persist: bool = True,
    ) -> None:
        self._memory_repository = memory_repository
        self._repository = turbovec_repository
        self._embedding_adapter = embedding_adapter or HashEmbeddingAdapter(dimensions)
        self._telemetry_service = telemetry_service
        self._compat = compat or TurboVecCompat()
        self._enabled = enabled
        self._index_name = _validate_index_name(index_name)
        self._index_dir = Path(index_dir)
        self._dimensions = dimensions
        self._bit_width = bit_width
        self._auto_persist = auto_persist
        self._indexes: dict[str, Any] = {}

    def remember(self, record: MemoryRecord) -> str:
        """Index a canonical memory record in a compressed vector index."""
        status = self.status(self._index_name)
        if not status.available:
            raise RuntimeError(status.reason or "turbovec_unavailable")
        if (
            self._memory_repository is not None
            and self._memory_repository.get(record.memory_id) is None
        ):
            raise ValueError(f"canonical memory record not found: {record.memory_id}")
        repository = self._require_repository()
        vector = self._embedding_adapter.embed_text(record.summary)
        index = self._runtime_index(status)
        vector_id = self._stable_vector_id(status.index_id, record.memory_id)
        self._compat.add_vectors(index, [vector], [vector_id])
        if self._auto_persist:
            self._compat.save_index(index, status.index_path)
        repository.upsert_entry(
            status.index_id,
            record.memory_id,
            vector_id,
            _source_text_hash(record.summary),
            record.owner_scope,
            record.memory_type,
        )
        self._emit(
            "memory_indexed",
            "memory",
            record.memory_id,
            0.6,
            {"adapter_name": self.adapter_name, "index_id": status.index_id},
        )
        return f"{status.index_id}-{record.memory_id}"

    def retrieve(self, query: SemanticMemoryQuery) -> list[SemanticMemoryResult]:
        """Retrieve memory records using compressed vector recall."""
        status = self.status(self._index_name)
        if not status.available:
            raise RuntimeError(status.reason or "turbovec_unavailable")
        if self._memory_repository is None:
            raise RuntimeError("canonical_memory_repository_required")
        repository = self._require_repository()
        entries = repository.list_active_entries(
            status.index_id,
            query.scope,
            [str(memory_type) for memory_type in query.memory_types],
            limit=max(query.limit * 5, 100),
        )
        if not entries:
            return []
        allowed_ids = [entry["vector_id"] for entry in entries]
        scores, vector_ids = self._compat.search(
            self._runtime_index(status),
            self._embedding_adapter.embed_text(query.query),
            max(query.limit * 5, query.limit),
            allowed_ids=allowed_ids,
        )
        entry_by_vector = {entry["vector_id"]: entry for entry in entries}
        results: list[SemanticMemoryResult] = []
        for score, vector_id in zip(scores, vector_ids, strict=True):
            entry = entry_by_vector.get(vector_id)
            if entry is None:
                continue
            record = self._memory_repository.get(entry["memory_id"])
            if record is None:
                continue
            clamped = _clamp(score)
            if query.min_score is not None and clamped < query.min_score:
                continue
            results.append(_result(record, clamped, query.query, status, entry))
            if len(results) >= query.limit:
                break
        for result in results:
            self._emit(
                "memory_node_activated",
                "memory",
                result.memory.memory_id,
                result.score,
                {"adapter_name": self.adapter_name, "index_id": status.index_id},
            )
        return results

    def forget(self, memory_id: str) -> bool:
        """Soft-delete a TurboVec index entry and remove the vector when possible."""
        status = self.status(self._index_name)
        if not status.available:
            return False
        repository = self._require_repository()
        entry = repository.get_entry_by_memory(status.index_id, memory_id)
        if entry is None:
            return False
        deleted = repository.soft_delete_entry(status.index_id, memory_id)
        try:
            self._compat.remove_ids(self._runtime_index(status), [entry["vector_id"]])
            if self._auto_persist:
                self._compat.save_index(self._runtime_index(status), status.index_path)
        except RuntimeError:
            pass
        return deleted

    def reindex(self, memory_id: str) -> SemanticIndexResponse:
        """Reindex one memory record from canonical memory."""
        if self._memory_repository is None:
            return _index_response(False, memory_id, None, "canonical_memory_repository_required")
        record = self._memory_repository.get(memory_id)
        if record is None:
            return _index_response(False, memory_id, None, "memory_not_found")
        embedding_id = self.remember(record)
        return _index_response(True, memory_id, embedding_id, None)

    def rebuild(self, request: TurboVecRebuildRequest) -> TurboVecRebuildResponse:
        """Rebuild a compressed index from canonical memory records."""
        index_name = _validate_index_name(request.index_name)
        status = self.status(index_name)
        if self._memory_repository is None:
            return _rebuild_response(False, request, 0, 0, 0, status, "memory_repository_missing")
        records = self._memory_repository.list_active(
            request.scope,
            limit=request.limit,
            memory_types=request.memory_types,
        )
        if request.dry_run:
            return _rebuild_response(
                False,
                request,
                len(records),
                0,
                0,
                status,
                status.reason if not status.available else None,
            )
        if not status.available:
            return _rebuild_response(False, request, 0, len(records), 0, status, status.reason)
        repository = self._require_repository()
        index = self._compat.create_index(self._dimensions, self._bit_width)
        indexed = 0
        failed = 0
        for record in records:
            try:
                vector_id = self._stable_vector_id(status.index_id, record.memory_id)
                self._compat.add_vectors(
                    index,
                    [self._embedding_adapter.embed_text(record.summary)],
                    [vector_id],
                )
                repository.upsert_entry(
                    status.index_id,
                    record.memory_id,
                    vector_id,
                    _source_text_hash(record.summary),
                    record.owner_scope,
                    record.memory_type,
                )
                indexed += 1
            except Exception:
                failed += 1
        self._indexes[index_name] = index
        if self._auto_persist:
            self._compat.save_index(index, status.index_path)
        status = repository.mark_rebuilt(status.index_id)
        self._emit(
            "memory_index_rebuilt",
            "index",
            status.index_id,
            0.8,
            {"indexed": indexed, "failed": failed},
        )
        return _rebuild_response(True, request, indexed, 0, failed, status, None)

    def status(self, index_name: str = "default") -> TurboVecIndexStatus:
        """Return TurboVec availability and index metadata."""
        safe_name = _validate_index_name(index_name)
        index_path = str(_safe_index_path(self._index_dir, safe_name))
        base = _status(
            index_name=safe_name,
            dimensions=self._dimensions,
            bit_width=self._bit_width,
            index_path=index_path,
            status="active",
            available=True,
            reason=None,
            entry_count=0,
        )
        if not self._enabled:
            return base.model_copy(
                update={
                    "status": "disabled",
                    "available": False,
                    "reason": "turbovec_disabled",
                }
            )
        if not self._compat.is_available():
            return base.model_copy(
                update={
                    "status": "unavailable",
                    "available": False,
                    "reason": self._compat.availability_reason() or "turbovec_package_unavailable",
                }
            )
        if self._repository is None:
            return base.model_copy(
                update={
                    "status": "unavailable",
                    "available": False,
                    "reason": "turbovec_repository_missing",
                }
            )
        try:
            existing = self._repository.create_or_get_index(
                safe_name,
                self._dimensions,
                self._bit_width,
                index_path,
            )
        except RuntimeError as exc:
            return base.model_copy(
                update={"status": "failed", "available": False, "reason": str(exc)}
            )
        return existing.model_copy(update={"available": existing.status == "active"})

    def _runtime_index(self, status: TurboVecIndexStatus) -> Any:
        index = self._indexes.get(status.index_name)
        if index is not None:
            return index
        try:
            if Path(status.index_path).exists():
                index = self._compat.load_index(status.index_path)
            else:
                index = self._compat.create_index(status.dimensions, status.bit_width)
        except RuntimeError as exc:
            raise RuntimeError(str(exc)) from exc
        self._indexes[status.index_name] = index
        return index

    def _stable_vector_id(self, index_id: str, memory_id: str) -> int:
        repository = self._require_repository()
        counter = 0
        while True:
            candidate = _stable_vector_id(memory_id if counter == 0 else f"{memory_id}:{counter}")
            existing = repository.get_entry_by_vector(index_id, candidate)
            if existing is None or existing["memory_id"] == memory_id:
                return candidate
            counter += 1

    def _require_repository(self) -> TurboVecRepository:
        if self._repository is None:
            raise RuntimeError("turbovec_repository_missing")
        return self._repository

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, object],
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-turbovec-{event_type}-{node_id}",
            trace_id=f"turbovec-{node_id}",
            event_type=cast(Any, event_type),
            node_type=cast(Any, node_type),
            node_id=node_id,
            edge_from=None,
            edge_to=None,
            intensity=_clamp(intensity),
            payload=payload,
            created_at=datetime.now(UTC),
        )
        emit = getattr(self._telemetry_service, "emit", None)
        save = getattr(self._telemetry_service, "save_visual_telemetry", None)
        try:
            if callable(emit):
                emit(event)
            elif callable(save):
                save(event.trace_id, [event])
        except Exception:
            return


def _index_response(
    indexed: bool,
    memory_id: str,
    embedding_id: str | None,
    reason: str | None,
) -> SemanticIndexResponse:
    return SemanticIndexResponse(
        indexed=indexed,
        memory_id=memory_id,
        adapter_name="turbovec",
        embedding_id=embedding_id,
        reason=reason,
    )


def _rebuild_response(
    rebuilt: bool,
    request: TurboVecRebuildRequest,
    indexed: int,
    skipped: int,
    failed: int,
    status: TurboVecIndexStatus,
    reason: str | None,
) -> TurboVecRebuildResponse:
    return TurboVecRebuildResponse(
        rebuilt=rebuilt,
        dry_run=request.dry_run,
        index_name=request.index_name,
        indexed=indexed,
        skipped=skipped,
        failed=failed,
        status=status,
        reason=reason,
    )


def _result(
    record: MemoryRecord,
    score: float,
    query: str,
    status: TurboVecIndexStatus,
    entry: TurboVecEntry,
) -> SemanticMemoryResult:
    return SemanticMemoryResult(
        memory=record,
        score=_clamp(score),
        retrieval_source="semantic_memory",
        adapter_name="turbovec",
        matched_terms=sorted(_tokens(query).intersection(_tokens(record.summary))),
        metadata={
            "index_id": status.index_id,
            "index_name": status.index_name,
            "vector_id": entry["vector_id"],
            "source_text_hash": entry["source_text_hash"],
        },
    )


def _status(
    *,
    index_name: str,
    dimensions: int,
    bit_width: int,
    index_path: str,
    status: str,
    available: bool,
    reason: str | None,
    entry_count: int,
) -> TurboVecIndexStatus:
    now = datetime.now(UTC)
    return TurboVecIndexStatus(
        index_id=f"turbovec-{index_name}",
        index_name=index_name,
        adapter_name="turbovec",
        dimensions=dimensions,
        bit_width=bit_width,
        index_path=index_path,
        status=cast(Any, status),
        entry_count=entry_count,
        available=available,
        reason=reason,
        metadata={},
        created_at=now,
        updated_at=now,
        rebuilt_at=None,
    )


def _stable_vector_id(memory_id: str) -> int:
    digest = hashlib.sha256(memory_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)


def _source_text_hash(text_value: str) -> str:
    return hashlib.sha256(text_value.encode("utf-8")).hexdigest()


def _validate_index_name(index_name: str) -> str:
    if not index_name or "/" in index_name or "\\" in index_name or ".." in index_name:
        raise ValueError("index_name cannot be empty or contain path traversal")
    return index_name


def _safe_index_path(index_dir: Path, index_name: str) -> Path:
    safe_dir = index_dir.expanduser()
    safe_dir.mkdir(parents=True, exist_ok=True)
    candidate = (safe_dir / f"{_validate_index_name(index_name)}.tvindex").resolve()
    root = safe_dir.resolve()
    if root not in candidate.parents:
        raise ValueError("index_path_outside_configured_directory")
    return candidate


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
