from __future__ import annotations

from operator_console_integration_test_support import (
    authorization_ledger,
    operator_auth,
    program_ledger,
)


def test_operator_console_authorization_is_sole_active_sri_authorization():
    auth = operator_auth()
    program = program_ledger()
    ledger = authorization_ledger()
    assert auth["authorization_transaction_id"] == "AION-236-SRI-0004"
    if ledger["program_state"] == "secure_runtime_integration_program_complete":
        assert ledger["authorization_active"] is False
        assert ledger["authorization_consumed"] is True
        assert ledger["authorization_expired"] is True
        assert ledger["authorization_closed_by_task"] == "AION-238"
        assert program["active_sri_implementation_authorization"] is None
        assert ledger["active_sri_implementation_authorization_count"] == 0
    else:
        assert auth["authorization_active"] is True
        assert auth["authorization_consumed"] is False
        assert auth["authorization_expired"] is False
        assert program["active_sri_implementation_authorization"] == "AION-236-SRI-0004"
        assert ledger["active_sri_implementation_authorization_count"] == 1
