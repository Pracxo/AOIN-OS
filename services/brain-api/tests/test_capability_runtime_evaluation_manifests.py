from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import (
    assert_scenario_passes,
    evaluation_module,
    evaluation_report,
)


def test_capability_manifest_registry_integrity_verified():
    module = evaluation_module()
    item = assert_scenario_passes("capability_manifest_registry_integrity")
    report = evaluation_report()

    assert tuple(report["capability_manifest_ids"]) == tuple(module.EXPECTED_CAPABILITIES)
    assert "manifest_tampering_detected" in {check["name"] for check in item["checks"]}


def test_connector_manifest_registry_integrity_verified():
    item = assert_scenario_passes("connector_manifest_registry_integrity")

    assert "connector_id_exact" in {check["name"] for check in item["checks"]}
