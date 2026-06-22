from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_concepts_api_create_list_get_and_archive() -> None:
    client = TestClient(create_app(kernel_container()))

    created = client.post(
        "/brain/concepts",
        json={
            "name": "Generic Concept",
            "description": "A generic concept.",
            "owner_scope": ["workspace:main"],
        },
    )
    assert created.status_code == 200
    concept_id = created.json()["concept_id"]

    listed = client.get("/brain/concepts", params={"scope": "workspace:main"})
    fetched = client.get(f"/brain/concepts/{concept_id}", params={"scope": "workspace:main"})
    archived = client.post(
        f"/brain/concepts/{concept_id}/archive",
        params={"scope": "workspace:main"},
        json={"reason": "test"},
    )

    assert listed.status_code == 200
    assert listed.json()[0]["concept_id"] == concept_id
    assert fetched.status_code == 200
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
