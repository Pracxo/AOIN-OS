from secure_runtime_aion232_test_helpers import scenario


def test_policy_risk_guardrail_and_approval_bindings_are_read_only() -> None:
    for scenario_id in (
        "policy_binding_integrity",
        "risk_binding_integrity",
        "guardrail_binding_integrity",
        "approval_evidence_and_separation_of_duties",
    ):
        reqs = scenario(scenario_id)["requirements"]
        assert all(reqs.values())
    approval = scenario("approval_evidence_and_separation_of_duties")["requirements"]
    assert approval["pre_existing_approval_only"] is True
    assert approval["runtime_creates_zero_approvals"] is True
    assert approval["approval_cannot_authorize_actual_execution"] is True
