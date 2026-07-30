from __future__ import annotations

from aion_brain.contracts.secure_runtime import SecureRuntimeKillSwitchStatus
from tests.secure_runtime_test_support import secure_runtime_fixture


def test_kill_switch_clear_then_active_is_session_scoped_and_terminal() -> None:
    fixture = secure_runtime_fixture()

    assert fixture.kill_switch.check().status == SecureRuntimeKillSwitchStatus.clear
    active = fixture.kill_switch.activate(
        reason_code="operator_stop",
        operator_identity_fingerprint=fixture.operator_identity.operator_identity_fingerprint,
    )
    assert active.status == SecureRuntimeKillSwitchStatus.active
    assert active.network_kill_switch is False
    assert active.global_process_singleton is False
