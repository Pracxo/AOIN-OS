"""Contract Registry API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_contract_registry_api_routes_work() -> None:
    client = TestClient(create_app(kernel_container()))

    seed = client.post(
        "/brain/contracts/rules/seed-defaults",
        json={"scope": ["workspace:main"], "dry_run": True},
    )
    snapshot = client.post(
        "/brain/contracts/snapshots",
        json={"scope": ["workspace:main"], "snapshot_type": "manual"},
    )
    snapshot_id = snapshot.json()["contract_snapshot_id"]
    snapshots = client.get("/brain/contracts/snapshots", params={"scope": "workspace:main"})
    fetched_snapshot = client.get(
        f"/brain/contracts/snapshots/{snapshot_id}",
        params={"scope": "workspace:main"},
    )
    contracts = client.get("/brain/contracts/contracts", params={"scope": "workspace:main"})
    interfaces = client.get("/brain/contracts/interfaces", params={"scope": "workspace:main"})
    rules = client.get("/brain/contracts/rules", params={"scope": "workspace:main"})
    scan = client.post(
        "/brain/contracts/compatibility/scan",
        json={
            "owner_scope": ["workspace:main"],
            "baseline_snapshot_id": snapshot_id,
            "candidate_snapshot_id": snapshot_id,
        },
    )
    fetched_scan = client.get(
        f"/brain/contracts/compatibility/scans/{scan.json()['compatibility_scan_id']}"
    )
    findings = client.get("/brain/contracts/findings")
    notes = client.get("/brain/contracts/migration-notes", params={"scope": "workspace:main"})
    report = client.post("/brain/contracts/report", json={"scope": ["workspace:main"]})

    for response in (
        seed,
        snapshot,
        snapshots,
        fetched_snapshot,
        contracts,
        interfaces,
        rules,
        scan,
        fetched_scan,
        findings,
        notes,
        report,
    ):
        assert response.status_code == 200
    assert seed.json()["dry_run"] is True
    assert snapshot.json()["metadata"]["source_mutated"] is False
    assert report.json()["contract_report_id"].startswith("contract-report-")
