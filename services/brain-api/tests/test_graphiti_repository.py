"""Graphiti metadata repository tests."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.memory.graphiti_repository import GraphitiRepository


def test_graphiti_repository_persists_config_and_sync_records() -> None:
    """Graphiti repository stores only AION-owned metadata."""
    repository = GraphitiRepository(engine=sqlite_engine())

    status = repository.create_or_get_config("default", "unknown", None)
    repository.record_sync(
        status.graphiti_config_id,
        "node",
        "node-1",
        "graphiti_node",
        "node-1",
        ["workspace:main"],
        "synced",
        {"adapter_name": "graphiti"},
    )

    records = repository.list_sync_records(status.graphiti_config_id, ["workspace:main"])

    assert repository.get_config("default") == status
    assert records[0]["source_type"] == "node"
    assert records[0]["source_id"] == "node-1"
    assert records[0]["metadata"] == {"adapter_name": "graphiti"}


def test_graphiti_repository_filters_scope_and_soft_deletes_records() -> None:
    """Sync records are scope-filtered and can be soft-deleted."""
    repository = GraphitiRepository(engine=sqlite_engine())
    status = repository.create_or_get_config("default", "unknown", None)
    repository.record_sync(
        status.graphiti_config_id,
        "edge",
        "edge-1",
        "graphiti_edge",
        "edge-1",
        ["workspace:main"],
        "synced",
        {},
    )

    assert repository.list_sync_records(status.graphiti_config_id, ["workspace:other"]) == []
    assert repository.soft_delete_sync_record(status.graphiti_config_id, "edge", "edge-1")
    assert repository.list_sync_records(status.graphiti_config_id, ["workspace:main"]) == []


def sqlite_engine():
    """Create an in-memory SQLite engine."""
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
