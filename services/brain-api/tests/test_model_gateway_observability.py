from __future__ import annotations

from aion_brain.model_gateway.observability import health_snapshot, observability_snapshot
from tests.model_gateway_aion233_test_support import NOW


def test_observability_and_health_are_redacted_and_ready_reference_only() -> None:
    obs = observability_snapshot(
        snapshot_id="observability-AION-233",
        session_id="gateway-session",
        event_counters={"reference_provider_simulations": 2},
        health_state="ready_reference_simulation",
        audit_chain_head="0" * 64,
        created_at=NOW,
    )
    health = health_snapshot(
        health_id="health-AION-233",
        health_state="ready_reference_simulation",
        created_at=NOW,
    )
    assert obs.redacted is True
    assert obs.raw_prompt_retained is False
    assert obs.raw_response_retained is False
    assert health.reference_provider_available is True
    assert health.actual_provider_calls_disabled is True
    assert health.network_egress_disabled is True
    assert health.credential_access_disabled is True
