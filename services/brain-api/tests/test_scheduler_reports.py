"""Scheduler report tests."""

from __future__ import annotations

from tests.scheduler_fakes import service_graph


def test_scheduler_report_service_creates_report() -> None:
    _, _, _, _, _, _, reports, *_ = service_graph()

    report = reports.create_report(["workspace:main"])

    assert report.status == "passed"
    assert report.metadata["no_target_execution"] is True
