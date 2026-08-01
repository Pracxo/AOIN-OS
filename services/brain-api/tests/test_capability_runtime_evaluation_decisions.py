from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import assert_scenario_passes


def test_policy_risk_guardrail_and_approval_decisions_verified():
    assert_scenario_passes("policy_binding_integrity")
    assert_scenario_passes("risk_binding_integrity")
    assert_scenario_passes("guardrail_binding_integrity")
    assert_scenario_passes("approval_evidence_and_separation_of_duties")
