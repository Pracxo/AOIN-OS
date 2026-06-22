"""Audit ledger and checkpoint tests."""

from __future__ import annotations

from aion_brain.audit_integrity.checkpoints import AuditCheckpointService
from aion_brain.contracts.audit_integrity import AuditRecordRequest
from tests.audit_integrity_fakes import ledger


def _request(action: str = "command.dispatch") -> AuditRecordRequest:
    return AuditRecordRequest(
        action_type=action,
        resource_type="command",
        event_type="command_created",
        outcome="completed",
        source_component="test",
        payload={"value": action},
    )


def test_audit_integrity_ledger_records_first_entry_with_no_previous_hash() -> None:
    service, _repo, _telemetry = ledger()

    entry = service.record(_request())

    assert entry.sequence_number == 1
    assert entry.previous_hash is None


def test_audit_integrity_ledger_chains_second_entry_to_first_hash() -> None:
    service, _repo, _telemetry = ledger()
    first = service.record(_request("command.dispatch"))
    second = service.record(_request("event.ingest"))

    assert second.sequence_number == 2
    assert second.previous_hash == first.entry_hash


def test_audit_integrity_ledger_creates_checkpoint_at_interval() -> None:
    service, repo, _telemetry = ledger(checkpoint_interval=2)
    service.record(_request("command.dispatch"))
    service.record(_request("event.ingest"))

    checkpoints = AuditCheckpointService(repo).list_checkpoints()

    assert checkpoints
    assert checkpoints[0].entry_count == 2
