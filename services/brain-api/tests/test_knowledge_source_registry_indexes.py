from __future__ import annotations

import pytest
from knowledge_source_registry_implementation_helpers import valid_batch
from pydantic import ValidationError

from aion_brain.knowledge_intelligence.source_registry_index import (
    SourceRegistryIndex,
    build_source_registry_index,
)


def test_source_registry_index_builds_deterministic_exact_indexes():
    records = valid_batch().records
    index = build_source_registry_index(records)
    assert index.record_ids == tuple(record.record_id for record in records)
    assert index.records_by_id[records[0].record_id] == (records[0].record_id,)
    snapshot = records[0].payload
    assert hasattr(snapshot, "snapshot_fingerprint")
    assert index.records_by_snapshot_fingerprint[snapshot.snapshot_fingerprint]
    assert index == build_source_registry_index(tuple(reversed(records)))


def test_source_registry_index_rejects_duplicate_or_missing_record_references():
    records = valid_batch().records
    index = build_source_registry_index(records)
    with pytest.raises(ValidationError):
        SourceRegistryIndex.model_validate(
            {**index.model_dump(), "records_by_id": {"missing": ("missing",)}}
        )
    with pytest.raises(ValidationError):
        SourceRegistryIndex.model_validate(
            {
                **index.model_dump(),
                "records_by_id": {records[0].record_id: (records[0].record_id,) * 2},
            }
        )
