from __future__ import annotations

import pytest

from aion_brain.contracts.secure_runtime import (
    SecureRuntimeSessionState,
    SecureRuntimeStageCommand,
)
from tests.secure_runtime_test_support import NOW, secure_runtime_fixture


def test_state_machine_accepts_only_explicit_next_transition() -> None:
    fixture = secure_runtime_fixture()
    command = SecureRuntimeStageCommand(
        command_id="command-AION-231",
        session_id=fixture.session.session_id,
        expected_current_state=SecureRuntimeSessionState.drafted,
        requested_next_state=SecureRuntimeSessionState.authorized,
        session_plan_fingerprint=fixture.session_plan.plan_fingerprint or "",
        input_fingerprints=(fixture.session_plan.plan_fingerprint or "",),
        operator_identity_fingerprint=fixture.operator_identity.operator_identity_fingerprint,
        created_at=NOW,
        expires_at=fixture.authorization.expires_at,
    )
    fixture.service.validate_stage_command(
        session=fixture.session,
        command=command,
        kill_switch_state=fixture.kill_switch_state,
        now=NOW,
    )


def test_state_machine_rejects_stage_skip() -> None:
    fixture = secure_runtime_fixture()
    command = SecureRuntimeStageCommand(
        command_id="command-skip-AION-231",
        session_id=fixture.session.session_id,
        expected_current_state=SecureRuntimeSessionState.drafted,
        requested_next_state=SecureRuntimeSessionState.session_active,
        session_plan_fingerprint=fixture.session_plan.plan_fingerprint or "",
        input_fingerprints=(fixture.session_plan.plan_fingerprint or "",),
        operator_identity_fingerprint=fixture.operator_identity.operator_identity_fingerprint,
        created_at=NOW,
        expires_at=fixture.authorization.expires_at,
    )
    with pytest.raises(ValueError, match="invalid secure-runtime state transition"):
        fixture.service.validate_stage_command(
            session=fixture.session,
            command=command,
            kill_switch_state=fixture.kill_switch_state,
            now=NOW,
        )
