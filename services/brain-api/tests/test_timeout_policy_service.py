from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aion_brain.contracts.run_supervision import RunTimeoutPolicy
from tests.run_supervision_fakes import RunFixture, run_request


def test_timeout_policy_detects_timeout_without_auto_cancel() -> None:
    fixture = RunFixture()
    run = fixture.supervision.create(
        run_request(deadline_at=datetime.now(UTC) - timedelta(seconds=1))
    )
    policy = RunTimeoutPolicy(
        timeout_policy_id="policy-1",
        name="default",
        description="Default",
        status="active",
        target_system="command_bus",
        run_type="command",
        timeout_seconds=1,
        stall_after_seconds=1,
        max_status_age_seconds=1,
        severity="high",
        action_on_timeout="report_only",
        owner_scope=["workspace:main"],
    )
    fixture.timeouts.create_policy(policy)

    blockers = fixture.timeouts.evaluate(run.run_supervision_id)
    updated = fixture.repository.get_run(run.run_supervision_id)

    assert blockers[0].reason == "run_timeout_detected"
    assert blockers[0].metadata["auto_cancelled"] is False
    assert updated is not None
    assert updated.status == "timed_out"
