"""Audit verifier tests."""

from __future__ import annotations

from aion_brain.audit_integrity.verifier import AuditVerifier
from aion_brain.contracts.audit_integrity import (
    AuditEntry,
    AuditRecordRequest,
    AuditVerificationRequest,
)
from tests.audit_integrity_fakes import ledger


def test_audit_verifier_passes_valid_chain() -> None:
    service, repo, _telemetry = ledger(checkpoint_interval=2)
    service.record(_request("command.dispatch"))
    service.record(_request("event.ingest"))

    run = AuditVerifier(repo).verify(AuditVerificationRequest())

    assert run.status == "passed"


def test_audit_verifier_detects_broken_previous_hash() -> None:
    service, repo, _telemetry = ledger()
    service.record(_request("command.dispatch"))
    repo.append_entry(
        AuditEntry(
            audit_entry_id="audit-bad",
            sequence_number=2,
            action_type="event.ingest",
            resource_type="event",
            event_type="event_accepted",
            outcome="completed",
            source_component="test",
            payload_hash="payload",
            previous_hash="wrong",
            entry_hash="entry-bad",
            hash_algorithm="sha256",
            canonical_payload={},
            redaction_metadata={},
            metadata={},
        )
    )

    run = AuditVerifier(repo).verify(AuditVerificationRequest(verify_payload_hashes=False))

    assert run.status == "failed"
    assert any(item["type"] == "previous_hash_mismatch" for item in run.violations)


def test_audit_verifier_detects_payload_hash_mismatch() -> None:
    service, repo, _telemetry = ledger()
    entry = service.record(_request("command.dispatch"))
    repo.append_entry(
        entry.model_copy(
            update={
                "audit_entry_id": "audit-bad-payload",
                "sequence_number": 2,
                "previous_hash": entry.entry_hash,
                "payload_hash": "wrong",
                "entry_hash": "entry-bad-payload",
            }
        )
    )

    run = AuditVerifier(repo).verify(AuditVerificationRequest())

    assert run.status == "failed"
    assert any(item["type"] == "payload_hash_mismatch" for item in run.violations)


def _request(action: str) -> AuditRecordRequest:
    return AuditRecordRequest(
        action_type=action,
        resource_type="command",
        event_type="command_created",
        outcome="completed",
        source_component="test",
        payload={"value": action},
    )
