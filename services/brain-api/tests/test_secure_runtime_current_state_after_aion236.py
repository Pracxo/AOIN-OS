from __future__ import annotations

from operator_console_integration_test_support import program_ledger

POST_AION236_STATE = (
    "capability_runtime_evaluated_operator_console_integration_authorized_not_implemented"
)


def test_secure_runtime_current_state_after_aion236():
    program = program_ledger()
    assert program["program_state"] == POST_AION236_STATE
    assert program["operator_console_integration_authorized"] is True
    assert program["operator_console_integration_implemented"] is False
    assert program["integrated_authenticated_local_pilot_authorized"] is True
    assert program["integrated_authenticated_local_pilot_completed"] is False
    assert program["production_runtime_authorized"] is False
    assert program["v02_release_ready"] is False
