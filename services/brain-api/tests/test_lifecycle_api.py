"""Lifecycle API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container
from tests.lifecycle_helpers import old_descriptor


def test_lifecycle_policy_api_round_trip_and_seed_defaults() -> None:
    client = TestClient(create_app(kernel_container()))

    seeded = client.post(
        "/brain/lifecycle/policies/seed-defaults",
        json={"scope": ["workspace:main"], "dry_run": True},
    )
    created = client.post(
        "/brain/lifecycle/policies",
        json={
            "lifecycle_policy_id": "lifecycle-policy-api",
            "name": "api-policy",
            "description": "Generic API lifecycle policy.",
            "owner_scope": ["workspace:main"],
            "rule": {"hard_delete_allowed": False},
        },
    )
    listed = client.get(
        "/brain/lifecycle/policies",
        params={"scope": "workspace:main"},
    )
    fetched = client.get(
        "/brain/lifecycle/policies/lifecycle-policy-api",
        params={"scope": "workspace:main"},
    )

    assert seeded.status_code == 200
    assert seeded.json()["dry_run"] is True
    assert created.status_code == 200
    assert listed.status_code == 200
    assert fetched.status_code == 200
    assert fetched.json()["lifecycle_policy_id"] == "lifecycle-policy-api"


def test_lifecycle_evaluate_api_is_advisory() -> None:
    client = TestClient(create_app(kernel_container()))
    client.post(
        "/brain/registry/resources",
        json={"descriptor": old_descriptor("res-api").model_dump(mode="json")},
    )

    response = client.post(
        "/brain/lifecycle/evaluate",
        json={"owner_scope": ["workspace:main"], "mode": "dry_run"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "dry_run"
    assert payload["resources_evaluated"] == 1
    assert payload["classifications_created"] == 1
    assert payload["result"]["source_records_mutated"] is False
    assert payload["result"]["hard_delete_allowed"] is False


def test_lifecycle_query_and_candidate_endpoints_work() -> None:
    client = TestClient(create_app(kernel_container()))

    classifications = client.get(
        "/brain/lifecycle/classifications",
        params={"scope": "workspace:main"},
    )
    archives = client.get(
        "/brain/lifecycle/archive-candidates",
        params={"scope": "workspace:main"},
    )
    redactions = client.get(
        "/brain/lifecycle/redaction-candidates",
        params={"scope": "workspace:main"},
    )
    purge = client.post(
        "/brain/lifecycle/purge-preview",
        json={"resource_uris": ["aion://generic/res-1"], "scope": ["workspace:main"]},
    )
    purge_list = client.get(
        "/brain/lifecycle/purge-previews",
        params={"scope": "workspace:main"},
    )
    report = client.post("/brain/lifecycle/report", json={"scope": ["workspace:main"]})
    reviews = client.get("/brain/lifecycle/reviews", params={"scope": "workspace:main"})

    assert classifications.status_code == 200
    assert archives.status_code == 200
    assert redactions.status_code == 200
    assert purge.status_code == 200
    assert purge.json()["hard_delete_allowed"] is False
    assert purge_list.status_code == 200
    assert report.status_code == 200
    assert reviews.status_code == 200
