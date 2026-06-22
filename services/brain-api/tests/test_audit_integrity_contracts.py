"""Audit integrity contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.audit_integrity import (
    AuditEntry,
    AuditExportRequest,
    AuditRecordRequest,
    ProvenanceLink,
)


def test_audit_entry_validates_sequence_number() -> None:
    with pytest.raises(ValidationError):
        AuditEntry(
            audit_entry_id="audit-1",
            sequence_number=0,
            action_type="command.dispatch",
            resource_type="command",
            event_type="command_created",
            outcome="completed",
            source_component="test",
            payload_hash="hash",
            previous_hash=None,
            entry_hash="entry",
            hash_algorithm="sha256",
            canonical_payload={},
            redaction_metadata={},
            metadata={},
        )


def test_audit_entry_rejects_non_sha256_hash_algorithm() -> None:
    with pytest.raises(ValidationError):
        AuditEntry(
            audit_entry_id="audit-1",
            sequence_number=1,
            action_type="command.dispatch",
            resource_type="command",
            event_type="command_created",
            outcome="completed",
            source_component="test",
            payload_hash="hash",
            previous_hash=None,
            entry_hash="entry",
            hash_algorithm="md5",
            canonical_payload={},
            redaction_metadata={},
            metadata={},
        )


def test_audit_record_request_rejects_secret_like_payload() -> None:
    with pytest.raises(ValidationError):
        AuditRecordRequest(
            action_type="command.dispatch",
            resource_type="command",
            event_type="command_created",
            outcome="completed",
            source_component="test",
            payload={"api_key": "secret"},
        )


def test_audit_record_request_strips_chain_of_thought() -> None:
    request = AuditRecordRequest(
        action_type="command.dispatch",
        resource_type="command",
        event_type="command_created",
        outcome="completed",
        source_component="test",
        payload={"safe": True, "chain_of_thought": "hidden"},
    )

    assert request.payload == {"safe": True}


def test_provenance_link_validates_relation_type() -> None:
    with pytest.raises(ValidationError):
        ProvenanceLink(
            provenance_link_id="prov-1",
            source_type="event",
            source_id="event-1",
            target_type="command",
            target_id="command-1",
            relation_type="domain_specific",  # type: ignore[arg-type]
            confidence=0.8,
        )


def test_audit_export_request_rejects_unsafe_output_dir() -> None:
    with pytest.raises(ValidationError):
        AuditExportRequest(owner_scope=["workspace:main"], output_dir="../audit")
