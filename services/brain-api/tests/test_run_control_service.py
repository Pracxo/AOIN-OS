from __future__ import annotations

from aion_brain.contracts.run_control import RunControlRequestCreateRequest
from tests.run_supervision_fakes import RunFixture, run_request


def test_control_dry_run_creates_planned_request() -> None:
    fixture = RunFixture()
    run = fixture.supervision.create(run_request())

    control = fixture.control.request_control(
        RunControlRequestCreateRequest(
            run_supervision_id=run.run_supervision_id,
            control_type="request_status",
            reason="check status",
        )
    )
    handed_off = fixture.control.handoff_control(control.run_control_request_id)

    assert control.status == "requested"
    assert handed_off.status == "completed"
    assert handed_off.result["planned_target_control"] is True
    assert handed_off.result["executed"] is False


def test_controlled_request_blocked_when_disabled_and_high_risk_waits_for_approval() -> None:
    fixture = RunFixture()
    run = fixture.supervision.create(run_request())

    blocked = fixture.control.request_control(
        RunControlRequestCreateRequest(
            run_supervision_id=run.run_supervision_id,
            control_type="pause",
            reason="pause",
            requested_mode="controlled",
        )
    )
    waiting = fixture.control.request_control(
        RunControlRequestCreateRequest(
            run_supervision_id=run.run_supervision_id,
            control_type="cancel",
            reason="cancel",
        )
    )

    assert blocked.status == "blocked"
    assert waiting.status == "waiting_for_approval"
    assert waiting.approval_request_id == "approval_required"
