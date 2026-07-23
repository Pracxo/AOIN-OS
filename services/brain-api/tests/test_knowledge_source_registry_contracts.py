from __future__ import annotations

from datetime import UTC, datetime

import pytest
from knowledge_source_registry_implementation_helpers import valid_batch
from pydantic import ValidationError

from aion_brain.contracts.knowledge_research import fingerprint_payload
from aion_brain.contracts.knowledge_source_registry import (
    PROGRAM_ID,
    RegisteredCitationReference,
    RegisteredPolicyDecision,
    RegisteredSourceSnapshotDigest,
    SourceRegistryRecordEnvelope,
    validate_source_registry_reason_codes,
)


def test_source_registry_contracts_accept_valid_payloads_and_envelopes():
    batch = valid_batch()
    assert batch.program_id == PROGRAM_ID
    assert batch.record_count == 6
    assert all(record.read_only and record.redacted for record in batch.records)


def test_source_registry_contracts_reject_extra_fields_and_malformed_fingerprints():
    citation = next(
        record.payload
        for record in valid_batch().records
        if isinstance(record.payload, RegisteredCitationReference)
    )
    with pytest.raises(ValidationError):
        RegisteredCitationReference.model_validate(
            {**citation.model_dump(mode="json"), "extra": "rejected"}
        )
    with pytest.raises(ValidationError):
        RegisteredCitationReference.model_validate(
            {**citation.model_dump(mode="json"), "citation_fingerprint": "bad"}
        )


def test_source_registry_contracts_reject_naive_non_utc_and_wrong_authorization():
    record = valid_batch().records[0]
    with pytest.raises(ValidationError):
        SourceRegistryRecordEnvelope.model_validate(
            {**record.model_dump(mode="json"), "created_at": datetime(2026, 7, 23, 12, 0)}
        )
    with pytest.raises(ValidationError):
        SourceRegistryRecordEnvelope.model_validate(
            {
                **record.model_dump(mode="json"),
                "created_at": datetime(2026, 7, 23, 13, 0).replace(tzinfo=UTC),
                "authorization_transaction_id": "AION-000-KI-0000",
            }
        )


def test_source_registry_contracts_are_immutable_and_reject_protected_material():
    record = valid_batch().records[0]
    with pytest.raises(ValidationError):
        SourceRegistryRecordEnvelope.model_validate(
            {
                **record.model_dump(mode="json"),
                "payload": {
                    **record.payload.model_dump(mode="json"),
                    "declared_title": "sk-secret",
                },
            }
        )
    with pytest.raises(ValidationError) as captured:
        RegisteredCitationReference.model_validate(
            {
                **valid_batch().records[2].payload.model_dump(mode="json"),
                "locator_value": "sk-secret",
            }
        )
    assert "sk-secret" not in str(captured.value)
    with pytest.raises(ValidationError):
        record.record_id = "changed"  # type: ignore[misc]


def test_source_registry_reason_codes_are_stable_unique_and_closed():
    assert validate_source_registry_reason_codes(("source_registry_batch_valid",))
    with pytest.raises(ValueError):
        validate_source_registry_reason_codes(("unknown",))
    with pytest.raises(ValueError):
        validate_source_registry_reason_codes(
            ("source_registry_batch_valid", "source_registry_batch_valid")
        )


def test_source_registry_policy_decision_payload_is_metadata_only():
    snapshot = valid_batch().records[0].payload
    assert isinstance(snapshot, RegisteredSourceSnapshotDigest)
    payload = {
        "policy_decision_id": "source-registry-policy-0001",
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_fingerprint": snapshot.snapshot_fingerprint,
        "source_class": snapshot.source_class,
        "robots_policy_status": snapshot.robots_policy_status,
        "licence_policy_status": snapshot.licence_policy_status,
        "reason_codes": ("source_registry_record_valid",),
        "created_at": snapshot.retrieval_timestamp,
    }
    fingerprint_payload_input = {
        **payload,
        "created_at": snapshot.retrieval_timestamp.isoformat(),
    }
    decision = RegisteredPolicyDecision(
        **payload,
        policy_decision_fingerprint=fingerprint_payload(fingerprint_payload_input),
    )
    assert decision.claim_verified is False
    assert decision.knowledge_promoted is False
    assert decision.belief_mutated is False
    assert decision.runtime_effect is False
