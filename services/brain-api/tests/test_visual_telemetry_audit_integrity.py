"""Visual telemetry audit integrity tests."""

from __future__ import annotations

from aion_brain.contracts.audit_integrity import AuditRecordRequest
from tests.audit_integrity_fakes import ledger


def test_visual_telemetry_emits_audit_events() -> None:
    service, _repo, telemetry = ledger()

    service.record(
        AuditRecordRequest(
            action_type="command.dispatch",
            resource_type="command",
            event_type="command_created",
            outcome="completed",
            source_component="test",
            payload={"value": "safe"},
        )
    )

    assert telemetry.events
    event = telemetry.events[0]
    assert event.event_type == "audit_entry_recorded"
    assert event.node_type == "audit"
