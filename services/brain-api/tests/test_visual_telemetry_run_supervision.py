from __future__ import annotations

from tests.run_supervision_fakes import RunFixture, run_request


def test_run_supervision_emits_visual_telemetry() -> None:
    fixture = RunFixture()
    record = fixture.supervision.create(run_request())
    fixture.sampler.sample(record.run_supervision_id, ["workspace:main"])

    event_types = {getattr(event, "event_type", None) for event in fixture.telemetry.events}

    assert "run_supervision_created" in event_types
    assert "run_status_sampled" in event_types
