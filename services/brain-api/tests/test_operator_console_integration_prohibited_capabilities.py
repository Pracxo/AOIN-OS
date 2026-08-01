from __future__ import annotations

from operator_console_integration_test_support import operator_auth


def test_all_operator_console_prohibited_capabilities_false():
    flags = operator_auth()["operator_console_prohibited_capabilities"]
    assert len(flags) == 73
    assert not any(flags.values())
    assert flags["public_listener_enabled"] is False
    assert flags["production_runtime_authorized"] is False
