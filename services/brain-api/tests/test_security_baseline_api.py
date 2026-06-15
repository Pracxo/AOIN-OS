"""Security baseline API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container

SCOPE = ["workspace:main"]


def test_security_scan_apis_work(tmp_path) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "app.py"
    target.write_text('API_KEY = "sk-apitest1234567890"\n', encoding="utf-8")
    client = TestClient(create_app(kernel_container()))

    run = client.post(
        "/brain/security/scans/run",
        json={"scan_type": "secrets", "owner_scope": SCOPE, "paths": [str(target)]},
    )
    assert run.status_code == 200
    scan_id = run.json()["security_scan_id"]

    assert client.get(f"/brain/security/scans/{scan_id}").status_code == 200
    assert client.get("/brain/security/scans").status_code == 200


def test_threat_model_apis_work() -> None:
    client = TestClient(create_app(kernel_container()))

    seeded = client.post(
        "/brain/security/threat-models/seed-defaults",
        json={"dry_run": False, "owner_scope": SCOPE},
    )
    listed = client.get("/brain/security/threat-models")
    threat_model_id = listed.json()[0]["threat_model_id"]
    updated = client.post(
        f"/brain/security/threat-models/{threat_model_id}/status",
        json={"status": "accepted", "actor_id": "dev-user", "reason": "accepted locally"},
    )

    assert seeded.status_code == 200
    assert listed.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["status"] == "accepted"


def test_security_controls_apis_work() -> None:
    client = TestClient(create_app(kernel_container()))

    seeded = client.post("/brain/security/controls/seed-defaults", json={"dry_run": False})
    listed = client.get("/brain/security/controls")
    control_key = listed.json()[0]["control_key"]
    updated = client.post(
        f"/brain/security/controls/{control_key}/status",
        json={"status": "implemented", "actor_id": "dev-user", "reason": "verified locally"},
    )

    assert seeded.status_code == 200
    assert listed.status_code == 200
    assert updated.status_code == 200


def test_hardening_gate_apis_work() -> None:
    client = TestClient(create_app(kernel_container()))
    client.post(
        "/brain/security/threat-models/seed-defaults",
        json={"dry_run": False, "owner_scope": SCOPE},
    )
    client.post("/brain/security/controls/seed-defaults", json={"dry_run": False})

    run = client.post(
        "/brain/security/hardening-gate/run",
        json={
            "owner_scope": SCOPE,
            "include_secret_scan": False,
            "include_api_exposure_check": False,
            "include_policy_coverage_check": False,
        },
    )
    gate_id = run.json()["hardening_gate_id"]

    assert run.status_code == 200
    assert client.get(f"/brain/security/hardening-gate/{gate_id}").status_code == 200
    assert client.get("/brain/security/hardening-gate").status_code == 200
