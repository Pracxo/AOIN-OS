from __future__ import annotations

from aion_brain.connector_runtime.blockers import (
    blockers_for_findings,
    disabled_runtime_blockers,
)


def test_disabled_runtime_blockers_cover_all_hard_off_boundaries() -> None:
    blocker_types = {item.blocker_type for item in disabled_runtime_blockers()}

    assert "connector_runtime_disabled" in blocker_types
    assert "external_calls_disabled" in blocker_types
    assert "credentials_disabled" in blocker_types
    assert "token_storage_disabled" in blocker_types
    assert "activation_disabled" in blocker_types
    assert "route_registration_disabled" in blocker_types


def test_blockers_for_findings_maps_unsafe_payloads() -> None:
    blockers = blockers_for_findings(
        [{"finding": "secret_detected"}, {"finding": "hidden_reasoning_detected"}],
        source_id="connector-egress-preview-test",
    )

    assert [item.blocker_type for item in blockers] == ["unsafe_payload", "unsafe_payload"]
    assert blockers[0].severity == "critical"
    assert blockers[1].severity == "high"
