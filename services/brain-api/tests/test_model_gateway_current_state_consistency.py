from __future__ import annotations

from secure_runtime_aion232_test_helpers import authorization, program


def test_current_state_marks_gateway_implemented_and_runtime_effects_disabled() -> None:
    payload = program()
    auth = authorization()
    assert payload["model_gateway_implemented"] is True
    assert payload["model_gateway_state"] == (
        "implemented_provider_neutral_reference_simulation_only"
    )
    assert payload["deterministic_reference_provider_available"] is True
    assert payload["local_model_gateway_simulation_pilot_completed"] is True
    active_state = (
        payload["active_sri_implementation_authorization"],
        payload["active_sri_implementation_task"],
        payload["formal_closeout_task"],
    )
    if payload["program_state"] == "secure_runtime_integration_program_complete":
        assert payload["active_sri_implementation_authorization_count"] == 0
        assert active_state == (None, None, None)
        assert payload["final_completed_task"] == "AION-238"
        assert payload["successor_authorization_id"] == "AION-238-V02RQ-0001"
        assert auth["authorization_active"] is False
        assert auth["authorization_consumed"] is True
        assert auth["authorization_expired"] is True
        assert auth["authorization_closed_by_task"] == "AION-238"
    else:
        assert active_state in {
            ("AION-234-SRI-0003", "AION-235", "AION-236"),
            ("AION-236-SRI-0004", "AION-237", "AION-238"),
        }
        assert auth["authorization_active"] is True
        assert auth["authorization_consumed"] is False
        assert auth["authorization_expired"] is False
    for key in (
        "actual_model_provider_call_enabled",
        "provider_network_egress_enabled",
        "provider_credential_read_enabled",
        "provider_credential_persistence_enabled",
        "live_model_session_enabled",
        "connector_execution_enabled",
        "actual_tool_execution_enabled",
        "production_runtime_authorized",
        "production_exposure",
        "v02_release_ready",
    ):
        assert payload[key] is False
