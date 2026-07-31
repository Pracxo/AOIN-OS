from __future__ import annotations

from aion234_test_support import load_json


def test_secure_runtime_current_state_after_aion235() -> None:
    program = load_json("docs/secure-runtime-integration/program-ledger.json")
    assert program["program_state"] == (
        "sandboxed_capability_runtime_implemented_reference_only_pending_closeout"
    )
    assert program["active_sri_implementation_authorization"] == "AION-234-SRI-0003"
    assert program["active_sri_implementation_task"] == "AION-235"
    assert program["formal_closeout_task"] == "AION-236"
    assert program["sandboxed_capability_runtime_authorized"] is True
    assert program["sandboxed_capability_runtime_implemented"] is True
    assert program["sandboxed_reference_capability_execution_available"] is True
    assert program["synthetic_reference_connector_simulation_available"] is True
    assert program["model_output_is_untrusted"] is True
    assert program["model_output_triggered_execution_enabled"] is False
    assert program["external_connector_execution_enabled"] is False
    assert program["external_tool_execution_enabled"] is False
    assert program["production_runtime_authorized"] is False
    assert program["production_exposure"] is False
    assert program["v02_release_ready"] is False
