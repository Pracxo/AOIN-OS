from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import (
    assert_scenario_passes,
    evaluation_module,
    evaluation_report,
)


def test_aion_235_delivery_and_ci_integrity_verified():
    module = evaluation_module()
    item = assert_scenario_passes("aion_235_delivery_and_ci_integrity")
    report = evaluation_report()

    assert report["implementation_pr"] == 154
    assert report["implementation_feature_commit"] == module.IMPLEMENTATION_FEATURE_COMMIT
    assert report["implementation_merge_commit"] == module.IMPLEMENTATION_MERGE_COMMIT
    assert {check["name"] for check in item["checks"]} >= {
        "implementation_pr_154_merged",
        "required_ci_checks_passed",
        "final_main_exact",
    }
