from __future__ import annotations

from operator_console_integration_test_support import operator_auth


def test_all_operator_console_authorized_capabilities_true():
    flags = operator_auth()["operator_console_authorized_capabilities"]
    assert len(flags) == 38
    assert all(flags.values())
    assert flags["integrated_authenticated_local_runtime_pilot_approved"] is True
