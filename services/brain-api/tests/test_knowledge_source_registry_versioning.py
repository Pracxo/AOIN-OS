from __future__ import annotations

import pytest
from knowledge_source_registry_implementation_helpers import correction_record, valid_batch

from aion_brain.knowledge_intelligence.source_registry_repository import (
    InMemorySourceRegistryRepository,
)


def test_source_registry_versioning_accepts_append_only_correction():
    batch = valid_batch()
    repository = InMemorySourceRegistryRepository().with_simulated_append(batch)
    correction = correction_record(
        batch.records[0],
        sequence_number=batch.record_count + 1,
        previous_record_fingerprint=batch.records[-1].record_fingerprint,
    )
    corrected = repository.with_simulated_append(
        batch.model_copy(update={"records": (correction,), "record_count": 1})
    )
    assert corrected.record_count() == batch.record_count + 1
    assert corrected.record_by_id(batch.records[0].record_id) == batch.records[0]


def test_source_registry_versioning_rejects_missing_self_or_invalid_version_correction():
    batch = valid_batch()
    repository = InMemorySourceRegistryRepository().with_simulated_append(batch)
    correction = correction_record(
        batch.records[0],
        sequence_number=batch.record_count + 1,
        previous_record_fingerprint=batch.records[-1].record_fingerprint,
    )
    invalid_records = [
        correction.model_construct(
            **{**correction.model_dump(), "supersedes_record_id": "missing-record"}
        ),
        correction.model_construct(
            **{**correction.model_dump(), "supersedes_record_id": correction.record_id}
        ),
        correction.model_construct(**{**correction.model_dump(), "record_version": 1}),
        correction.model_construct(**{**correction.model_dump(), "record_version": 99}),
    ]
    for invalid in invalid_records:
        with pytest.raises(ValueError):
            repository.with_simulated_append(
                batch.model_copy(update={"records": (invalid,), "record_count": 1})
            )
