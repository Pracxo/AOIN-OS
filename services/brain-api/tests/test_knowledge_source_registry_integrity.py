from __future__ import annotations

from knowledge_source_registry_implementation_helpers import valid_batch

from aion_brain.knowledge_intelligence.source_registry_integrity import (
    audit_source_registry,
)


def test_source_registry_integrity_audit_passes_valid_chain():
    report = audit_source_registry(valid_batch().records)
    assert report.status == "passed"
    assert report.validated_record_count == 6
    assert report.findings == ()


def test_source_registry_integrity_audit_detects_sequence_and_fingerprint_defects():
    records = list(valid_batch().records)
    gap = records[1].model_construct(**{**records[1].model_dump(), "sequence_number": 99})
    duplicate = records[1].model_construct(**{**records[1].model_dump(), "sequence_number": 1})
    bad_fingerprint = records[1].model_construct(
        **{**records[1].model_dump(), "record_fingerprint": "b" * 64}
    )
    bad_previous = records[1].model_construct(
        **{**records[1].model_dump(), "previous_record_fingerprint": "c" * 64}
    )
    for changed in (gap, duplicate, bad_fingerprint, bad_previous):
        report = audit_source_registry((records[0], changed, *records[2:]))
        assert report.status == "failed"


def test_source_registry_integrity_audit_detects_unresolved_reference_and_prohibited_state():
    records = list(valid_batch().records)
    unresolved = records[2].model_construct(
        **{
            **records[2].model_dump(),
            "payload": records[2].payload.model_construct(
                **{**records[2].payload.model_dump(), "snapshot_id": "missing-snapshot"}
            ),
        }
    )
    source_body = records[0].model_construct(
        **{**records[0].model_dump(), "source_body_bytes": 1}
    )
    for changed in (unresolved, source_body):
        report = audit_source_registry((records[0], records[1], changed, *records[3:]))
        assert report.status == "failed"
