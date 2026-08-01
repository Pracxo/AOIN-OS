from __future__ import annotations

from operator_console_integration_test_support import program_ledger


def test_aion_234_authorization_closed_as_consumed_by_aion_235():
    record = program_ledger()["aion_234_record"]
    assert record["authorization_state"] == "consumed_by_AION-235_closed_by_AION-236"
    assert record["authorization_consumed"] is True
    assert record["authorization_expired"] is True
    assert record["authorization_reusable"] is False
    assert record["authorization_consumed_by_prs"] == [154]
