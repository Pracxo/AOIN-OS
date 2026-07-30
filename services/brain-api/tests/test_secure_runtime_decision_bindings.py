from __future__ import annotations

from tests.secure_runtime_test_support import secure_runtime_fixture


def test_policy_risk_and_guardrail_bindings_are_read_only_and_exact() -> None:
    fixture = secure_runtime_fixture()

    assert fixture.policy_binding.decision_outcome == "allow_require_approval"
    assert fixture.risk_binding.decision_outcome == "require_approval"
    assert fixture.guardrail_binding.decision_outcome == "allow"
    assert fixture.risk_binding.computed_risk.value == "medium"
    assert fixture.guardrail_binding.blocked is False
    assert fixture.policy_binding.read_only is True
    assert fixture.risk_binding.runtime_effect is False
