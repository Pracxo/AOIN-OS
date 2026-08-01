from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import (
    assert_scenario_passes,
    evaluation_module,
    evaluation_report,
)


def test_pilot_evidence_schema_and_fingerprint_verified():
    module = evaluation_module()
    item = assert_scenario_passes("pilot_evidence_schema_and_fingerprint")
    report = evaluation_report()

    assert report["pilot_evidence_fingerprint"] == module.EXPECTED_PILOT_FINGERPRINT
    assert "generated_pilot_matches_committed_evidence" in {
        check["name"] for check in item["checks"]
    }
