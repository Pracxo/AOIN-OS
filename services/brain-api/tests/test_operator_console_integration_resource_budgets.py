from __future__ import annotations

from operator_console_integration_test_support import operator_auth


def test_operator_console_resource_limits_and_zero_limits():
    limits = operator_auth()["operator_console_resource_limits"]
    assert limits["maximum_operator_console_sessions"] == 1
    assert limits["maximum_routes"] == 10
    assert limits["maximum_static_assets"] == 5
    assert limits["maximum_public_listeners"] == 0
    assert limits["maximum_external_network_egress_calls"] == 0
    assert limits["maximum_git_operations"] == 0
