from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import assert_scenario_passes


def test_parent_component_lineage_integrity_verified():
    item = assert_scenario_passes("parent_component_lineage_integrity")

    assert {check["name"] for check in item["checks"]} >= {
        "secure_runtime_component_binding_present",
        "model_gateway_proposal_binding_present",
        "model_output_execution_authority_false",
    }
