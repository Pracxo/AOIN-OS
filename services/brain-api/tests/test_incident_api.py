from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_incident_apis_work() -> None:
    client = TestClient(create_app(kernel_container()))
    signal_payload = {
        "incident_signal_id": "signal-1",
        "trace_id": "trace-1",
        "source_type": "run_supervision",
        "source_id": "run-1",
        "signal_type": "stalled",
        "severity": "high",
        "title": "Run stalled",
        "summary": "A supervised run stalled.",
        "owner_scope": ["workspace:main"],
    }

    signal = client.post("/brain/incidents/signals", json=signal_payload)
    listed = client.get("/brain/incidents/signals", params={"scope": "workspace:main"})
    dry_run = client.post(
        "/brain/incidents/correlate",
        json={"owner_scope": ["workspace:main"], "mode": "dry_run"},
    )
    controlled = client.post(
        "/brain/incidents/correlate",
        json={"owner_scope": ["workspace:main"], "mode": "controlled"},
    )
    incident_id = controlled.json()["incidents"][0]["incident_id"]
    root_causes = client.post(
        f"/brain/incidents/{incident_id}/root-cause-candidates/generate",
        json={"scope": ["workspace:main"]},
    )
    review = client.post(
        "/brain/incidents/recovery-reviews",
        json={"incident_id": incident_id, "owner_scope": ["workspace:main"]},
    )
    query = client.post("/brain/incidents/query", json={"scope": ["workspace:main"]})
    acknowledged = client.post(
        f"/brain/incidents/{incident_id}/acknowledge",
        json={"reason": "reviewed"},
    )

    assert signal.status_code == 200
    assert listed.status_code == 200
    assert dry_run.status_code == 200
    assert dry_run.json()["incidents_created"] == 0
    assert controlled.status_code == 200
    assert controlled.json()["result"]["source_records_mutated"] is False
    assert root_causes.status_code == 200
    assert review.status_code == 200
    assert query.status_code == 200
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "acknowledged"


def test_kernel_registers_incident_services_diagnostics_routes_and_contracts() -> None:
    container = kernel_container()
    names = {record.service_name for record in container.service_registry.list_services()}
    checks = {check.name: check.status for check in container.diagnostics.run()}
    exported = container.contract_export_service.export_contracts(create_app(container))

    assert "incident_signal_service" in names
    assert "incident_service" in names
    assert "incident_correlation_engine" in names
    assert "root_cause_candidate_service" in names
    assert "recovery_review_service" in names
    assert checks["incident_signal_service_present"] == "passed"
    assert checks["incident_services_present"] == "passed"
    assert "/brain/incidents" in exported.openapi["paths"]
    assert "/brain/incidents/correlate" in exported.openapi["paths"]
    assert "IncidentSignal" in exported.contracts
    assert "IncidentRecord" in exported.contracts
    assert "RootCauseCandidate" in exported.contracts
    assert "RecoveryReview" in exported.contracts
