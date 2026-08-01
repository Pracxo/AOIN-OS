from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import assert_scenario_passes


def test_restricted_input_and_output_schema_integrity_verified():
    item = assert_scenario_passes("restricted_input_and_output_schema_integrity")

    assert {check["name"] for check in item["checks"]} >= {
        "malformed_external_ref_rejected",
        "content_encoding_rejected",
        "pattern_properties_rejected",
        "unsafe_input_rejected",
    }
