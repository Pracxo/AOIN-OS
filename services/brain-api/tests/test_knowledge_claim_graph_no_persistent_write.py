from __future__ import annotations

from aion_brain.knowledge_intelligence.claim_graph import ControlledTemporalClaimEvidenceGraph


def test_persistent_write_requests_fail_closed() -> None:
    decision = ControlledTemporalClaimEvidenceGraph().reject_persistent_write(1)
    assert decision.append_allowed is False
    assert decision.persistent_write_requested is True
    assert decision.persistent_write_applied is False
    assert "claim_graph_persistent_write_disabled" in decision.reason_codes
