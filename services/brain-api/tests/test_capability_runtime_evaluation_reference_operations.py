from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import assert_scenario_passes


def test_pure_reference_capability_execution_verified():
    item = assert_scenario_passes("pure_reference_capability_execution")

    assert {check["name"] for check in item["checks"]} >= {
        "six_reference_capabilities_executed",
        "normalization_exact",
        "sha256_exact_lowercase",
        "json_validation_deterministic",
    }
