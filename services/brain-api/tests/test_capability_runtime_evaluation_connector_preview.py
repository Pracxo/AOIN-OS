from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import assert_scenario_passes


def test_synthetic_connector_read_preview_and_rollback_verified():
    assert_scenario_passes("synthetic_reference_connector_read")
    assert_scenario_passes("synthetic_write_preview_and_rollback")
