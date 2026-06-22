"""Operator API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_operator_apis_work() -> None:
    client = TestClient(create_app(kernel_container()))

    overview = client.post("/brain/operator/overview", json={"owner_scope": ["workspace:main"]})
    cards = client.get("/brain/operator/status-cards", params={"scope": "workspace:main"})
    queues = client.get("/brain/operator/queues", params={"scope": "workspace:main"})
    actions = client.get("/brain/operator/actions", params={"scope": "workspace:main"})
    readiness = client.get("/brain/operator/readiness", params={"scope": "workspace:main"})
    runbooks = client.get("/brain/operator/runbooks")
    snapshot = client.post("/brain/operator/snapshots", json={"owner_scope": ["workspace:main"]})
    acknowledgement = client.post(
        "/brain/operator/actions/acknowledge",
        json={"source_type": "generic", "source_id": "item-1", "reason": "seen"},
    )

    assert overview.status_code == 200
    assert cards.status_code == 200
    assert queues.status_code == 200
    assert actions.status_code == 200
    assert readiness.status_code == 200
    assert runbooks.status_code == 200
    assert snapshot.status_code == 200
    assert acknowledgement.status_code == 200
    fetched = client.get(
        f"/brain/operator/snapshots/{snapshot.json()['operator_snapshot_id']}",
        params={"scope": "workspace:main"},
    )
    assert fetched.status_code == 200


def test_operator_api_acknowledgement_only_records_acknowledgement() -> None:
    client = TestClient(create_app(kernel_container()))

    response = client.post(
        "/brain/operator/actions/acknowledge",
        json={"source_type": "generic", "source_id": "item-1", "reason": "seen"},
    )
    listed = client.get("/brain/operator/acknowledgements")

    assert response.status_code == 200
    assert listed.status_code == 200
    assert listed.json()[0]["source_id"] == "item-1"
