from __future__ import annotations

import pytest
from knowledge_source_registry_implementation_helpers import valid_batch

from aion_brain.knowledge_intelligence.source_registry_repository import (
    InMemorySourceRegistryRepository,
)


def test_source_registry_repository_is_immutable_and_simulated_append_is_pure():
    batch = valid_batch()
    original = InMemorySourceRegistryRepository()
    appended = original.with_simulated_append(batch)
    assert original.record_count() == 0
    assert appended.record_count() == batch.record_count
    assert appended.snapshot() == batch.records
    assert appended.record_by_id(batch.records[0].record_id) == batch.records[0]


def test_source_registry_repository_has_no_mutating_or_persistence_methods():
    repository = InMemorySourceRegistryRepository()
    for name in (
        "update",
        "delete",
        "truncate",
        "compact",
        "overwrite",
        "save",
        "commit_to_file",
        "database_connect",
        "database_migrate",
    ):
        assert not hasattr(repository, name)


def test_source_registry_repository_rejects_sequence_or_changed_payload_append():
    batch = valid_batch()
    repository = InMemorySourceRegistryRepository().with_simulated_append(batch)
    changed = batch.records[0].model_construct(
        **{**batch.records[0].model_dump(), "record_fingerprint": "b" * 64}
    )
    changed_batch = batch.model_copy(update={"records": (changed,), "record_count": 1})
    with pytest.raises(ValueError):
        repository.with_simulated_append(changed_batch)
