from __future__ import annotations

from aion_brain.contracts.secure_runtime import (
    ZERO_FINGERPRINT,
    SecureRuntimeGuardOutcome,
    SecureRuntimeKillSwitchState,
    SecureRuntimeKillSwitchStatus,
)
from tests.secure_runtime_test_support import NOW, secure_runtime_fixture


def test_runtime_guard_allows_simulation_only_after_all_bindings() -> None:
    fixture = secure_runtime_fixture()

    assert fixture.guard_decision.outcome == SecureRuntimeGuardOutcome.allow_simulation
    assert fixture.guard_decision.allow_execution is False
    assert fixture.guard_decision.production_effect is False


def test_runtime_guard_kills_when_kill_switch_active() -> None:
    fixture = secure_runtime_fixture()
    active = SecureRuntimeKillSwitchState(
        session_id=fixture.session.session_id,
        status=SecureRuntimeKillSwitchStatus.active,
        reason_code="operator_stop",
        activation_fingerprint=ZERO_FINGERPRINT,
        operator_identity_fingerprint=fixture.operator_identity.operator_identity_fingerprint,
        created_at=NOW,
    )
    decision = fixture.service.evaluate_runtime_guard(
        authorization_envelope=fixture.authorization,
        operator_identity_binding=fixture.operator_identity,
        request_identity_binding=fixture.request_identity,
        actor_context_binding=fixture.actor_context,
        session=fixture.session,
        request=fixture.request,
        capability_plan=fixture.capability_plan,
        policy_binding=fixture.policy_binding,
        risk_binding=fixture.risk_binding,
        guardrail_binding=fixture.guardrail_binding,
        approval_bundle=fixture.approval_bundle,
        side_effect_budget_decision=fixture.budget_decision,
        kill_switch_state=active,
        created_at=NOW,
    )
    assert decision.outcome == SecureRuntimeGuardOutcome.kill
