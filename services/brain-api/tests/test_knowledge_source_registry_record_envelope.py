from __future__ import annotations

import pytest
from knowledge_source_registry_implementation_helpers import (
    correction_record,
    valid_batch,
)
from pydantic import ValidationError

from aion_brain.contracts.knowledge_source_registry import (
    SourceRegistryRecordEnvelope,
)
from aion_brain.knowledge_intelligence.source_registry_integrity import (
    validate_record_envelope,
)


def test_source_registry_record_envelope_validates_payload_and_record_fingerprints():
    record = valid_batch().records[0]
    assert validate_record_envelope(record) == record
    with pytest.raises(ValidationError):
        SourceRegistryRecordEnvelope.model_validate(
            {**record.model_dump(mode="json"), "payload_fingerprint": "a" * 64}
        )
    broken = SourceRegistryRecordEnvelope.model_construct(
        **{**record.model_dump(), "record_fingerprint": "b" * 64}
    )
    with pytest.raises(ValueError):
        validate_record_envelope(broken)


def test_source_registry_record_envelope_sequence_version_and_supersession_rules():
    batch = valid_batch()
    first = batch.records[0]
    correction = correction_record(
        first,
        sequence_number=len(batch.records) + 1,
        previous_record_fingerprint=batch.records[-1].record_fingerprint,
    )
    assert correction.record_version == 2
    assert correction.supersedes_record_id == first.record_id
    with pytest.raises(ValidationError):
        SourceRegistryRecordEnvelope.model_validate(
            {
                **first.model_dump(mode="json"),
                "record_version": 1,
                "supersedes_record_id": first.record_id,
            }
        )
    with pytest.raises(ValidationError):
        SourceRegistryRecordEnvelope.model_validate(
            {**correction.model_dump(mode="json"), "supersedes_record_id": None}
        )


def test_source_registry_record_envelope_carries_no_runtime_or_persistent_write_state():
    for record in valid_batch().records:
        assert record.source_body_present is False
        assert record.source_body_bytes == 0
        assert record.claim_verified is False
        assert record.knowledge_promoted is False
        assert record.belief_created is False
        assert record.belief_mutated is False
        assert record.persistent_write_applied is False
        assert record.runtime_effect is False
