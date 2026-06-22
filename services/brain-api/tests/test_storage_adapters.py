"""Object storage adapter tests."""

import pytest

from aion_brain.storage.in_memory_store import InMemoryObjectStore
from aion_brain.storage.local_store import LocalObjectStore
from aion_brain.storage.minio_adapter import MinIOAdapter


def test_in_memory_object_store_stores_and_retrieves_bytes() -> None:
    """In-memory storage is deterministic for tests."""
    store = InMemoryObjectStore()

    ref = store.put_bytes(b"alpha", "text/plain", {"kind": "test"})

    assert ref.content_ref.startswith("memory://objects/")
    assert store.get_bytes(ref.content_ref) == b"alpha"
    assert store.delete(ref.content_ref) is True


def test_local_object_store_stores_bytes_under_configured_root(tmp_path) -> None:
    """Local storage writes under the configured root."""
    store = LocalObjectStore(str(tmp_path))

    ref = store.put_bytes(b"alpha", "text/plain", {})

    assert ref.content_ref.startswith("local://objects/")
    assert store.get_bytes(ref.content_ref) == b"alpha"
    assert any(tmp_path.iterdir())


def test_minio_adapter_is_placeholder_only() -> None:
    """MinIO adapter remains a dependency-free placeholder."""
    adapter = MinIOAdapter()

    assert "AION contracts must remain independent" in (MinIOAdapter.__doc__ or "")
    with pytest.raises(NotImplementedError):
        adapter.get_bytes("minio://objects/test")
