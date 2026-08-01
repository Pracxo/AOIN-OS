from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import assert_scenario_passes


def test_model_output_non_authority_and_operator_selection_verified():
    item = assert_scenario_passes("model_output_non_authority_and_operator_selection")

    assert {check["name"] for check in item["checks"]} >= {
        "model_output_cannot_trigger_dispatch",
        "explicit_operator_selection_required",
        "operator_selected_every_success",
        "automatic_selection_zero",
    }
