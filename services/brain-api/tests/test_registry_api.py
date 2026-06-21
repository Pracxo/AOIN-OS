"""Registry API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container
from tests.resource_registry_helpers import descriptor


def test_registry_resource_api_round_trip() -> None:
    client = TestClient(create_app(kernel_container()))
    body = {"descriptor": descriptor().model_dump(mode="json")}

    created = client.post("/brain/registry/resources", json=body)
    assert created.status_code == 200
    resource_uri = created.json()["descriptor"]["resource_uri"]

    fetched = client.get(
        "/brain/registry/resources/by-uri",
        params={"resource_uri": resource_uri, "scope": "workspace:main"},
    )

    assert fetched.status_code == 200
    assert fetched.json()["descriptor"]["resource_uri"] == resource_uri


def test_registry_query_api_returns_resources() -> None:
    client = TestClient(create_app(kernel_container()))
    client.post(
        "/brain/registry/resources", json={"descriptor": descriptor().model_dump(mode="json")}
    )

    response = client.post(
        "/brain/registry/query",
        json={"scope": ["workspace:main"], "limit": 10},
    )

    assert response.status_code == 200
    assert response.json()["total_count"] == 1


def test_registry_validate_api_works() -> None:
    client = TestClient(create_app(kernel_container()))
    response = client.post(
        "/brain/registry/validate",
        json={"owner_scope": ["workspace:main"], "mode": "dry_run"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "dry_run"


def test_registry_snapshot_api_works() -> None:
    client = TestClient(create_app(kernel_container()))

    response = client.post("/brain/registry/snapshots", json={"scope": ["workspace:main"]})

    assert response.status_code == 200
    assert response.json()["snapshot_type"] == "manual"
