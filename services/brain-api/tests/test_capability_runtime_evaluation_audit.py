from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import assert_scenario_passes


def test_audit_observability_health_and_integrity_verified():
    assert_scenario_passes("audit_chain_integrity")
    assert_scenario_passes("observability_health_and_integrity")
    assert_scenario_passes("determinism_concurrency_redaction_and_performance")
