from __future__ import annotations

from tests.run_supervision_fakes import SCOPE, RunFixture, old_datetime, run_request


def test_sampler_persists_sample_and_updates_current_status() -> None:
    fixture = RunFixture()
    record = fixture.supervision.create(run_request())
    sample = fixture.sampler.sample(record.run_supervision_id, SCOPE)
    updated = fixture.repository.get_run(record.run_supervision_id)

    assert sample.observed_status == "running"
    assert updated is not None
    assert updated.current_status == "running"
    assert updated.last_sample_id == sample.run_status_sample_id


def test_sampler_detects_stalled_run() -> None:
    fixture = RunFixture()
    record = fixture.supervision.create(run_request())
    fixture.repository.save_run(
        record.model_copy(update={"last_seen_at": old_datetime(), "current_status": "running"})
    )

    fixture.sampler.sample(record.run_supervision_id, SCOPE)
    updated = fixture.repository.get_run(record.run_supervision_id)

    assert updated is not None
    assert updated.stalled is True
    assert updated.status == "stalled"
