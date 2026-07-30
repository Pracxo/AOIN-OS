from __future__ import annotations

from test_secure_runtime_integration_program_charter import (
    AUTHORIZED_CAPABILITIES,
    load_json,
)


def test_every_aion231_authorized_capability_is_recorded_true() -> None:
    program = load_json("docs/secure-runtime-integration/program-ledger.json")
    auth = load_json("docs/secure-runtime-integration/authorization-ledger.json")

    for payload in (program, auth):
        assert set(payload["authorized_capabilities"]) == set(AUTHORIZED_CAPABILITIES)
        assert all(
            payload["authorized_capabilities"][key] is True
            for key in AUTHORIZED_CAPABILITIES
        )


def test_static_console_records_authorized_sri_capability_projection() -> None:
    program = load_json("operator-console-static/demo-data/secure-runtime-integration-program.json")
    authorization = load_json(
        "operator-console-static/demo-data/secure-runtime-integration-authorization.json"
    )
    session = load_json("operator-console-static/demo-data/secure-runtime-integration-session.json")

    assert program["active_sri_implementation_authorization"] == "AION-230-SRI-0001"
    assert authorization["authorization_active"] is True
    assert authorization["implementation_task"] == "AION-231"
    assert session["operator_invoked"] is True
    assert session["local_session"] is True
    assert session["production_runtime"] is False
