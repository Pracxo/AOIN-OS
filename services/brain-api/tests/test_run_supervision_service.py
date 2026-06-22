from __future__ import annotations

import pytest

from tests.run_supervision_fakes import DenyPolicy, RunFixture, run_request


def test_run_supervision_service_creates_record_through_policy() -> None:
    fixture = RunFixture()
    record = fixture.supervision.create(run_request())

    assert record.status == "active"
    assert record.target_system == "command_bus"
    assert fixture.repository.get_run(record.run_supervision_id) is not None
    assert any(
        getattr(event, "event_type", None) == "run_supervision_created"
        for event in fixture.telemetry.events
    )


def test_policy_deny_blocks_supervision_create() -> None:
    fixture = RunFixture(policy=DenyPolicy())

    with pytest.raises(PermissionError):
        fixture.supervision.create(run_request())
