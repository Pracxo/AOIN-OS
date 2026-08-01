from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import (
    assert_scenario_passes,
    evaluation_report,
)


def test_zero_external_effects_and_repository_boundary_verified():
    assert_scenario_passes("zero_external_effects_and_repository_boundary")

    assert all(value == 0 for value in evaluation_report()["prohibited_effect_counters"].values())


def test_controlled_operator_console_integration_readiness_verified_without_source():
    item = assert_scenario_passes("controlled_operator_console_integration_readiness")

    assert "operator_console_source_not_created" in {check["name"] for check in item["checks"]}
