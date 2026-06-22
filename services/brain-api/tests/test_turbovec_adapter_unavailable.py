"""TurboVec adapter disabled and unavailable behavior."""

import importlib
import sys
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.memory import MemoryRecord, SemanticMemoryQuery, TurboVecRebuildRequest
from aion_brain.memory.repository import MemoryRepository
from aion_brain.memory.turbovec_adapter import TurboVecSemanticMemoryAdapter
from aion_brain.memory.turbovec_compat import TurboVecCompat
from aion_brain.memory.turbovec_repository import TurboVecRepository


def test_turbovec_adapter_status_returns_disabled_when_feature_off(tmp_path) -> None:
    """Disabled TurboVec reports clean disabled status."""
    adapter = TurboVecSemanticMemoryAdapter(index_dir=str(tmp_path), enabled=False)

    status = adapter.status()

    assert status.available is False
    assert status.reason == "turbovec_disabled"
    with pytest.raises(RuntimeError, match="turbovec_disabled"):
        adapter.retrieve(SemanticMemoryQuery(query="alpha", scope=["workspace:main"]))


def test_turbovec_adapter_status_returns_package_unavailable(monkeypatch, tmp_path) -> None:
    """Enabled TurboVec reports package unavailable without real dependency."""
    _force_missing_turbovec(monkeypatch)
    adapter = TurboVecSemanticMemoryAdapter(index_dir=str(tmp_path), enabled=True)

    status = adapter.status()

    assert status.available is False
    assert status.reason == "turbovec_package_unavailable"


def test_turbovec_rebuild_dry_run_counts_memories_without_package(monkeypatch, tmp_path) -> None:
    """Dry run counts eligible canonical memory even when package is unavailable."""
    _force_missing_turbovec(monkeypatch)
    memory_repository = MemoryRepository(engine=_engine())
    memory_repository.save(_memory("memory-1", "alpha", ["workspace:main"]))
    adapter = TurboVecSemanticMemoryAdapter(
        memory_repository=memory_repository,
        turbovec_repository=TurboVecRepository(engine=_engine()),
        compat=TurboVecCompat(),
        enabled=True,
        index_dir=str(tmp_path),
    )

    response = adapter.rebuild(
        TurboVecRebuildRequest(scope=["workspace:main"], dry_run=True, limit=10)
    )

    assert response.dry_run is True
    assert response.indexed == 1
    assert response.reason == "turbovec_package_unavailable"


def _engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _force_missing_turbovec(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "turbovec", raising=False)
    original_import = importlib.import_module

    def fake_import(name: str):
        if name == "turbovec":
            raise ModuleNotFoundError(name)
        return original_import(name)

    monkeypatch.setattr(importlib, "import_module", fake_import)


def _memory(memory_id: str, summary: str, scope: list[str]) -> MemoryRecord:
    return MemoryRecord(
        memory_id=memory_id,
        memory_type="semantic",
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
