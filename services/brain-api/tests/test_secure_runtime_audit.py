from __future__ import annotations

from aion_brain.contracts.secure_runtime import InMemorySecureRuntimeAuditLedger


def test_audit_ledger_is_append_only_hash_chain() -> None:
    ledger = InMemorySecureRuntimeAuditLedger()
    first = ledger.append(session_id="session-AION-231", event_type="session_started")
    second = ledger.append(
        session_id="session-AION-231",
        event_type="simulated_dispatch_completed",
        decision_fingerprints=(first.audit_hash or "",),
    )

    assert second.prior_audit_hash == first.audit_hash
    assert ledger.verify_chain("session-AION-231") is True
