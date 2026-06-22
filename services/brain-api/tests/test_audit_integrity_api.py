"""Audit integrity API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_audit_api_record_list_verify_export_and_provenance_work(tmp_path) -> None:
    client = TestClient(create_app(kernel_container()))

    record = client.post(
        "/brain/audit/entries",
        json={
            "action_type": "command.dispatch",
            "resource_type": "command",
            "event_type": "command_created",
            "outcome": "completed",
            "source_component": "api_test",
            "payload": {"value": "safe"},
        },
    )
    listed = client.get("/brain/audit/entries")
    status = client.get("/brain/audit/status")
    verify = client.post("/brain/audit/verify", json={})
    export = client.post(
        "/brain/audit/export",
        json={
            "owner_scope": ["workspace:main"],
            "output_dir": str(tmp_path),
            "dry_run": True,
        },
    )
    provenance = client.post(
        "/brain/provenance/links",
        json={
            "provenance_link_id": "prov-api",
            "trace_id": "trace-api",
            "source_type": "event",
            "source_id": "event-api",
            "target_type": "command",
            "target_id": "command-api",
            "relation_type": "caused",
            "confidence": 0.9,
            "evidence_refs": [],
            "metadata": {},
        },
    )
    trace = client.get("/brain/provenance/traces/trace-api")

    assert record.status_code == 200
    assert record.json()["sequence_number"] >= 1
    assert listed.status_code == 200
    assert status.json()["latest_sequence"] >= 1
    assert verify.status_code == 200
    assert export.status_code == 200
    assert provenance.status_code == 200
    assert trace.status_code == 200
    assert trace.json()[0]["provenance_link_id"] == "prov-api"
