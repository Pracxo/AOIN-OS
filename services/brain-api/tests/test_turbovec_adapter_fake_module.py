"""TurboVec adapter behavior with a fake optional package."""

import sys
from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.memory import MemoryRecord, SemanticMemoryQuery, TurboVecRebuildRequest
from aion_brain.memory.repository import MemoryRepository
from aion_brain.memory.turbovec_adapter import TurboVecSemanticMemoryAdapter
from aion_brain.memory.turbovec_compat import TurboVecCompat
from aion_brain.memory.turbovec_repository import TurboVecRepository
from tests.turbovec_fakes import fake_idmap_module


def test_turbovec_adapter_indexes_retrieves_and_forgets_with_fake_module(
    monkeypatch,
    tmp_path,
) -> None:
    """TurboVec path returns AION semantic results without vendor objects."""
    monkeypatch.setitem(sys.modules, "turbovec", fake_idmap_module())
    memory_repository = MemoryRepository(engine=_engine())
    turbovec_repository = TurboVecRepository(engine=_engine())
    first = _memory("memory-1", "alpha beta", ["workspace:main"])
    second = _memory("memory-2", "gamma delta", ["workspace:main"])
    memory_repository.save(first)
    memory_repository.save(second)
    adapter = _adapter(memory_repository, turbovec_repository, tmp_path)

    first_embedding = adapter.remember(first)
    adapter.remember(second)
    results = adapter.retrieve(
        SemanticMemoryQuery(query="alpha beta", scope=["workspace:main"], limit=2)
    )
    status = adapter.status()

    assert first_embedding.startswith("turbovec-default-memory-1")
    assert results[0].memory.memory_id == "memory-1"
    assert results[0].adapter_name == "turbovec"
    assert results[0].metadata["index_name"] == "default"
    assert status.available is True
    assert status.entry_count == 2
    assert adapter.forget("memory-1") is True
    assert [
        result.memory.memory_id
        for result in adapter.retrieve(
            SemanticMemoryQuery(query="alpha beta", scope=["workspace:main"], limit=2)
        )
    ] == ["memory-2"]


def test_turbovec_rebuild_filters_scope_and_memory_type(monkeypatch, tmp_path) -> None:
    """Rebuild indexes only canonical memory records allowed by the request."""
    monkeypatch.setitem(sys.modules, "turbovec", fake_idmap_module())
    memory_repository = MemoryRepository(engine=_engine())
    turbovec_repository = TurboVecRepository(engine=_engine())
    memory_repository.save(_memory("memory-1", "alpha beta", ["workspace:main"]))
    memory_repository.save(
        _memory("memory-2", "alpha procedural", ["workspace:main"], memory_type="procedural")
    )
    memory_repository.save(_memory("memory-3", "alpha other", ["workspace:other"]))
    adapter = _adapter(memory_repository, turbovec_repository, tmp_path)

    response = adapter.rebuild(
        TurboVecRebuildRequest(
            scope=["workspace:main"],
            memory_types=["semantic"],
            limit=10,
        )
    )
    results = adapter.retrieve(
        SemanticMemoryQuery(query="alpha beta", scope=["workspace:main"], limit=10)
    )

    assert response.rebuilt is True
    assert response.indexed == 1
    assert response.failed == 0
    assert [result.memory.memory_id for result in results] == ["memory-1"]


def test_turbovec_reindex_reports_missing_memory_and_success(monkeypatch, tmp_path) -> None:
    """Single-record reindex uses canonical memory as the source of truth."""
    monkeypatch.setitem(sys.modules, "turbovec", fake_idmap_module())
    memory_repository = MemoryRepository(engine=_engine())
    turbovec_repository = TurboVecRepository(engine=_engine())
    memory_repository.save(_memory("memory-1", "alpha beta", ["workspace:main"]))
    adapter = _adapter(memory_repository, turbovec_repository, tmp_path)

    missing = adapter.reindex("missing")
    indexed = adapter.reindex("memory-1")

    assert missing.indexed is False
    assert missing.reason == "memory_not_found"
    assert indexed.indexed is True
    assert indexed.adapter_name == "turbovec"


def _adapter(
    memory_repository: MemoryRepository,
    turbovec_repository: TurboVecRepository,
    tmp_path,
) -> TurboVecSemanticMemoryAdapter:
    return TurboVecSemanticMemoryAdapter(
        memory_repository=memory_repository,
        turbovec_repository=turbovec_repository,
        compat=TurboVecCompat(),
        enabled=True,
        index_dir=str(tmp_path),
        dimensions=4,
        auto_persist=False,
    )


def _engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _memory(
    memory_id: str,
    summary: str,
    scope: list[str],
    *,
    memory_type: str = "semantic",
) -> MemoryRecord:
    return MemoryRecord(
        memory_id=memory_id,
        memory_type=memory_type,
        owner_scope=scope,
        source_event_id=None,
        content_ref=None,
        summary=summary,
        confidence=0.9,
        sensitivity="low",
        created_at=datetime.now(UTC),
        expires_at=None,
        metadata={},
    )
