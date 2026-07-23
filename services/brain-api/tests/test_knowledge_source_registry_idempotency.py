from __future__ import annotations

import pytest
from knowledge_source_registry_implementation_helpers import valid_batch

from aion_brain.knowledge_intelligence.source_registry_repository import (
    InMemorySourceRegistryRepository,
)


def test_source_registry_idempotent_replay_keeps_existing_records():
    batch = valid_batch()
    repository = InMemorySourceRegistryRepository().with_simulated_append(batch)
    replayed = repository.with_simulated_append(batch)
    assert replayed.record_count() == repository.record_count()
    assert replayed.records() == repository.records()


def test_source_registry_idempotency_rejects_changed_payload_for_same_record_id():
    batch = valid_batch()
    repository = InMemorySourceRegistryRepository().with_simulated_append(batch)
    changed = batch.records[0].model_construct(
        **{
            **batch.records[0].model_dump(),
            "record_fingerprint": "d" * 64,
            "payload_fingerprint": "e" * 64,
        }
    )
    with pytest.raises(ValueError):
        repository.with_simulated_append(
            batch.model_copy(update={"records": (changed,), "record_count": 1})
        )
