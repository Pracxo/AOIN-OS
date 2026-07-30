from __future__ import annotations

from aion_brain.contracts.secure_runtime import SecureRuntimeSessionState
from tests.secure_runtime_test_support import secure_runtime_fixture


def test_session_plan_is_operator_invoked_and_ephemeral() -> None:
    fixture = secure_runtime_fixture()

    assert fixture.session_plan.operator_invoked is True
    assert fixture.session_plan.automatic_continuation is False
    assert fixture.session_plan.background_execution is False
    assert fixture.session_plan.scheduled_execution is False
    assert fixture.session_plan.production_runtime is False
    assert fixture.session.current_state == SecureRuntimeSessionState.drafted
