from __future__ import annotations

from secure_runtime_aion232_test_helpers import authorization, load_json, program


def test_every_aion231_foundation_capability_remains_recorded_true() -> None:
    for payload in (program(), authorization()):
        caps = payload["foundation_authorized_capabilities"]
        assert all(caps.values())
        assert caps["local_operator_runtime_authorization_envelope_approved"] is True
        assert caps["runtime_guard_approved"] is True


def test_static_console_records_historical_aion231_and_current_gateway_projection() -> None:
    old_program = load_json(
        "operator-console-static/demo-data/secure-runtime-integration-program.json"
    )
    gateway = load_json("operator-console-static/demo-data/model-gateway-authorization.json")
    session = load_json("operator-console-static/demo-data/secure-runtime-integration-session.json")
    assert old_program["active_sri_implementation_authorization"] == "AION-230-SRI-0001"
    assert gateway["authorization_transaction_id"] == "AION-232-SRI-0002"
    assert gateway["authorization_active"] is True
    assert gateway["implementation_task"] == "AION-233"
    assert session["operator_invoked"] is True
    assert session["local_session"] is True
    assert session["production_runtime"] is False
