from __future__ import annotations

from aion_brain.contracts.secure_runtime import SecureSideEffectUsage, evaluate_side_effect_budget
from tests.secure_runtime_test_support import secure_runtime_fixture


def test_zero_effect_budget_passes_for_simulation_usage() -> None:
    fixture = secure_runtime_fixture()

    assert fixture.budget_decision.allowed is True
    assert fixture.usage.prohibited_effects_zero() is True


def test_one_external_call_fails_budget() -> None:
    fixture = secure_runtime_fixture()
    usage = SecureSideEffectUsage(model_provider_calls=1)
    decision = evaluate_side_effect_budget(budget=fixture.side_effect_budget, usage=usage)

    assert decision.allowed is False
    assert "prohibited_effect:model_provider_calls" in decision.reason_codes
