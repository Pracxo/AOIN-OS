"""Release Package integration with Contract Registry."""

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
from tests.release_package_fakes import packager


def test_release_package_includes_contract_registry_summary(tmp_path) -> None:  # type: ignore[no-untyped-def]
    repo = repository()
    repo.save_snapshot(snapshot("snapshot-1", interfaces=[interface_record()]))
    repo.save_finding(drift_finding())
    service = ContractRegistryReportService(repo, AllowPolicy())
    release_packager = packager(tmp_path)
    release_packager.set_contract_registry_services(repository=repo, report_service=service)

    summary = release_packager._contract_registry_summary(SCOPE)

    assert summary["available"] is True
    assert summary["snapshot"]["contract_snapshot_id"] == "snapshot-1"
    assert summary["report"]["status"] == "failed"
