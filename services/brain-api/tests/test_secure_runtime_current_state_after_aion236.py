from __future__ import annotations

from operator_console_integration_test_support import program_ledger

POST_AION236_STATE = (
    "capability_runtime_evaluated_operator_console_integration_authorized_not_implemented"
)
POST_AION237_STATE = (
    "operator_console_integrated_local_runtime_implemented_pending_final_evaluation"
)


def test_secure_runtime_current_state_after_aion236():
    program = program_ledger()
    assert program["program_state"] in {POST_AION236_STATE, POST_AION237_STATE}
    aion237_implemented = program["program_state"] == POST_AION237_STATE
    assert program["operator_console_integration_authorized"] is True
    assert program["operator_console_integration_implemented"] is aion237_implemented
    assert program["integrated_authenticated_local_pilot_authorized"] is True
    assert program["integrated_authenticated_local_pilot_completed"] is aion237_implemented
    assert program["production_runtime_authorized"] is False
    assert program["v02_release_ready"] is False
