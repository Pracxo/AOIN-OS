"""Bootstrap API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_bootstrap_api_sequence() -> None:
    client = TestClient(create_app(kernel_container()))
    scope = ["workspace:main"]

    profile_seed = client.post(
        "/brain/bootstrap/profiles/seed-defaults",
        json={"scope": scope, "dry_run": True},
    )
    assert profile_seed.status_code == 200
    assert profile_seed.json()["dry_run"] is True

    profiles = client.get("/brain/bootstrap/profiles", params={"scope": scope})
    assert profiles.status_code == 200
    assert any(item["profile_key"] == "local.dev" for item in profiles.json())

    bundle_seed = client.post(
        "/brain/bootstrap/seed-bundles/seed-defaults",
        json={"scope": scope, "dry_run": False},
    )
    assert bundle_seed.status_code == 200

    seed = client.post(
        "/brain/bootstrap/seed",
        json={"owner_scope": scope, "seed_bundle_key": "core.defaults"},
    )
    assert seed.status_code == 200
    assert seed.json()["status"] == "dry_run"

    doctor = client.post(
        "/brain/bootstrap/doctor",
        json={
            "owner_scope": scope,
            "include_golden_path": False,
            "include_release_smoke": False,
            "create_findings": True,
        },
    )
    assert doctor.status_code == 200
    assert doctor.json()["metadata"]["external_calls"] is False

    run = client.post(
        "/brain/bootstrap/run",
        json={
            "owner_scope": scope,
            "mode": "dry_run",
            "run_golden_path": False,
            "run_release_smoke": False,
            "run_setup_doctor": True,
            "create_notifications": False,
            "create_operator_items": False,
        },
    )
    assert run.status_code == 200
    body = run.json()
    assert body["mode"] == "dry_run"
    assert body["result"]["external_calls"] is False

    assert client.get("/brain/bootstrap/runs", params={"scope": scope}).status_code == 200
    assert client.get("/brain/bootstrap/findings", params={"scope": scope}).status_code == 200
    assert client.get("/brain/bootstrap/reports", params={"scope": scope}).status_code == 200


def test_bootstrap_api_rejects_external_metadata() -> None:
    client = TestClient(create_app(kernel_container()))

    response = client.post(
        "/brain/bootstrap/run",
        json={
            "owner_scope": ["workspace:main"],
            "metadata": {"enable_external_providers": True},
        },
    )

    assert response.status_code == 422
