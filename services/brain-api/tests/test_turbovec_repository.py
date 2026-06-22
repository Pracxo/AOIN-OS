"""TurboVec repository tests."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.memory.turbovec_repository import TurboVecRepository


def test_turbovec_repository_persists_index_and_entries() -> None:
    """Repository returns contracts and typed dicts, not SQLAlchemy rows."""
    repository = TurboVecRepository(engine=_engine())
    status = repository.create_or_get_index("default", 4, 4, "/tmp/default.tvindex")

    repository.upsert_entry(
        status.index_id,
        "memory-1",
        123,
        "hash-1",
        ["workspace:main"],
        "semantic",
    )

    stored = repository.get_index("default")
    assert stored is not None
    assert stored.entry_count == 1
    assert repository.get_entry_by_memory(status.index_id, "memory-1")["vector_id"] == 123
    assert repository.get_entry_by_vector(status.index_id, 123)["memory_id"] == "memory-1"
    assert len(repository.list_active_entries(status.index_id, ["workspace:main"])) == 1
    assert repository.list_active_entries(status.index_id, ["workspace:other"]) == []
    assert repository.soft_delete_entry(status.index_id, "memory-1") is True
    assert repository.list_active_entries(status.index_id, ["workspace:main"]) == []


def _engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
