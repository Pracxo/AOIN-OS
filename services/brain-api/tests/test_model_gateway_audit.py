from __future__ import annotations

from aion_brain.model_gateway.audit import InMemoryModelGatewayAuditLedger
from tests.model_gateway_aion233_test_support import NOW


def test_audit_ledger_is_append_only_redacted_hash_chain() -> None:
    ledger = InMemoryModelGatewayAuditLedger()
    first = ledger.append(
        session_id="gateway-session",
        event_type="authorization_validated",
        outcome="allowed",
        payload={"safe": True},
        created_at=NOW,
    )
    second = ledger.append(
        session_id="gateway-session",
        event_type="session_closed",
        outcome="closed",
        payload={"safe": True},
        created_at=NOW,
    )
    assert first.previous_record_fingerprint == "0" * 64
    assert second.previous_record_fingerprint == first.record_fingerprint
    assert ledger.chain_head("gateway-session") == second.record_fingerprint
    assert second.raw_prompt_retained is False
    assert second.raw_response_retained is False
