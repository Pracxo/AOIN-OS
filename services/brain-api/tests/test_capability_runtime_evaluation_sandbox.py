from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import assert_scenario_passes


def test_in_memory_sandbox_isolation_verified():
    item = assert_scenario_passes("in_memory_sandbox_isolation")

    assert {check["name"] for check in item["checks"]} >= {
        "in_memory_static_dispatch",
        "network_dns_disabled",
        "dynamic_eval_exec_disabled",
        "credentials_tokens_disabled",
    }
