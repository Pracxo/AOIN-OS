from __future__ import annotations

import pytest
from capability_runtime_test_support import new_service


def test_exact_replay_returns_existing_result_and_changed_replay_is_rejected() -> None:
    runtime, service, session = new_service()
    first = service.execute(
        session_id=session.session_id,
        request_id="replay-001",
        capability_id="capability.hash.sha256",
        input_payload={"text": "same"},
    )
    replay = service.execute(
        session_id=session.session_id,
        request_id="replay-001",
        capability_id="capability.hash.sha256",
        input_payload={"text": "same"},
    )
    assert replay.receipt.receipt_fingerprint == first.receipt.receipt_fingerprint
    assert service.counters["exact_replays_returned"] == 1
    with pytest.raises(runtime.CapabilityRuntimeRejected, match="changed replay"):
        service.execute(
            session_id=session.session_id,
            request_id="replay-001",
            capability_id="capability.hash.sha256",
            input_payload={"text": "changed"},
        )
    assert service.counters["changed_replays_rejected"] == 1


def test_model_output_unknown_capability_and_active_kill_switch_fail_closed() -> None:
    runtime, service, session = new_service()
    with pytest.raises(runtime.CapabilityRuntimeRejected):
        service.execute(
            session_id=session.session_id,
            request_id="model-trigger",
            capability_id="capability.text.normalize",
            input_payload={"text": "blocked"},
            model_output_triggered=True,
        )
    with pytest.raises(runtime.CapabilityRuntimeRejected):
        service.execute(
            session_id=session.session_id,
            request_id="unknown-capability",
            capability_id="capability.unknown",
            input_payload={},
        )
    with pytest.raises(runtime.CapabilityRuntimeRejected):
        service.execute(
            session_id=session.session_id,
            request_id="kill-switch",
            capability_id="capability.text.normalize",
            input_payload={"text": "blocked"},
            parent_kill_switch_active=True,
        )
    assert service.counters["model_output_triggered_executions_blocked"] == 1
    assert service.counters["unknown_capabilities_blocked"] == 1
