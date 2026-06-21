"""Contract registry report service tests."""

from __future__ import annotations

from aion_brain.contract_registry.reports import ContractRegistryReportService
from tests.contract_registry_helpers import (
    SCOPE,
    AllowPolicy,
    drift_finding,
    interface_record,
    repository,
    snapshot,
)


def test_contract_registry_report_service_counts_breaking_findings() -> None:
    repo = repository()
    repo.save_snapshot(snapshot("snapshot-1", interfaces=[interface_record()]))
    repo.save_finding(drift_finding())
    service = ContractRegistryReportService(repo, AllowPolicy())

    report = service.generate(SCOPE)

    assert report.status == "failed"
    assert report.active_breaking_findings == 1
    assert "resolve_breaking_findings" in report.recommendations
