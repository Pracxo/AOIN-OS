from __future__ import annotations

from aion_brain.contracts.run_supervision import RunSupervisionReportRequest
from tests.run_supervision_fakes import RunFixture, run_request


def test_run_supervision_report_counts_and_recommends() -> None:
    fixture = RunFixture()
    run = fixture.supervision.create(run_request())
    fixture.repository.save_run(run.model_copy(update={"status": "failed"}))

    report = fixture.reports.generate(RunSupervisionReportRequest(owner_scope=["workspace:main"]))

    assert report.failed_count == 1
    assert "review_failed_runs" in report.recommendations
