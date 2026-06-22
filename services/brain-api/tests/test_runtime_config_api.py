"""Runtime configuration API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container

SCOPE = ["workspace:main"]


def test_runtime_config_apis_work() -> None:
    client = TestClient(create_app(kernel_container()))

    created = client.post(
        "/brain/runtime-config/profiles",
        json={
            "name": "local",
            "description": "local profile",
            "owner_scope": SCOPE,
        },
    )
    profile_id = created.json()["config_profile_id"]
    listed = client.get("/brain/runtime-config/profiles")
    activated = client.post(
        f"/brain/runtime-config/profiles/{profile_id}/activate",
        json={"actor_id": "dev-user", "reason": "activate"},
    )
    disabled = client.post(
        f"/brain/runtime-config/profiles/{profile_id}/disable",
        json={"actor_id": "dev-user", "reason": "disable"},
    )
    override = client.post(
        "/brain/runtime-config/feature-overrides",
        json={
            "feature_key": "runtime_config.feature_overrides",
            "enabled": False,
            "owner_scope": SCOPE,
            "reason": "api test",
        },
    )

    assert created.status_code == 200
    assert client.get(f"/brain/runtime-config/profiles/{profile_id}").status_code == 200
    assert listed.status_code == 200
    assert activated.status_code == 200
    assert disabled.status_code == 200
    assert override.status_code == 200
    assert client.get("/brain/runtime-config/feature-overrides").status_code == 200


def test_snapshot_compare_and_validate_apis_work() -> None:
    client = TestClient(create_app(kernel_container()))
    first = client.post("/brain/runtime-config/snapshots", json={"owner_scope": SCOPE})
    second = client.post("/brain/runtime-config/snapshots", json={"owner_scope": SCOPE})
    compared = client.post(
        "/brain/runtime-config/snapshots/compare",
        json={
            "snapshot_id_a": first.json()["config_snapshot_id"],
            "snapshot_id_b": second.json()["config_snapshot_id"],
        },
    )
    validated = client.post("/brain/runtime-config/validate", json={"owner_scope": SCOPE})
    status = client.get("/brain/runtime-config/status", params={"scope": SCOPE})

    assert first.status_code == 200
    assert second.status_code == 200
    assert compared.status_code == 200
    assert validated.status_code == 200
    assert status.status_code == 200
