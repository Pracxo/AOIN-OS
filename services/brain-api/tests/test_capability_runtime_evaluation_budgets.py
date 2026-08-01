from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import assert_scenario_passes


def test_budget_and_kill_switch_enforcement_verified():
    assert_scenario_passes("side_effect_and_resource_budget_enforcement")
    assert_scenario_passes("parent_kill_switch_and_guard_precedence")
