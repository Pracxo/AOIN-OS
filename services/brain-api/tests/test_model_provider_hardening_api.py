"""Model provider hardening API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_model_provider_hardening_api_endpoints_work() -> None:
    client = TestClient(create_app(kernel_container()))
    profile = client.post(
        "/brain/model-providers/profiles",
        json={
            "provider_key": "generic.metadata_only",
            "name": "Generic",
            "description": "Generic metadata profile.",
            "owner_scope": ["workspace:main"],
        },
    )
    seed = client.post(
        "/brain/model-providers/profiles/seed-defaults",
        json={"scope": ["workspace:main"], "dry_run": True},
    )
    listed = client.get(
        "/brain/model-providers/profiles",
        params={"scope": "workspace:main"},
    )
    fetched = client.get(
        f"/brain/model-providers/profiles/{profile.json()['provider_profile_id']}",
        params={"scope": "workspace:main"},
    )
    preview = client.post(
        "/brain/model-providers/egress-preview",
        json={
            "provider_key": "generic.metadata_only",
            "owner_scope": ["workspace:main"],
            "prompt_summary": {"section_count": 1},
        },
    )
    simulation = client.post(
        "/brain/model-providers/simulate",
        json={
            "provider_key": "generic.metadata_only",
            "owner_scope": ["workspace:main"],
            "simulated_request": {"input_manifest_ref": "manifest-1"},
            "expected_response_shape": {"type": "object", "grounded": True},
        },
    )
    readiness = client.post(
        "/brain/model-providers/readiness",
        json={
            "provider_key": "generic.metadata_only",
            "owner_scope": ["workspace:main"],
            "simulation_refs": [simulation.json()["provider_simulation_id"]],
        },
    )
    blockers = client.get(
        "/brain/model-providers/blockers",
        params={"scope": "workspace:main"},
    )
    query = client.post(
        "/brain/model-providers/query",
        json={"scope": ["workspace:main"]},
    )

    responses = [
        profile,
        seed,
        listed,
        fetched,
        preview,
        simulation,
        readiness,
        blockers,
        query,
    ]
    assert [item.status_code for item in responses] == [200] * 9
    assert seed.json()["dry_run"] is True
    assert preview.json()["external_call_allowed"] is False
    assert simulation.json()["model_invoked"] is False
    assert readiness.json()["external_call_ready"] is False
    assert query.json()["metadata"]["external_model_calls_enabled"] is False
