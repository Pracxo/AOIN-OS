"""Conformance API tests."""

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_conformance_api_sequence() -> None:
    client = TestClient(create_app(kernel_container()))
    slot_response = client.post(
        "/brain/module-slots",
        json={
            "slot_key": "test.echo",
            "name": "Echo Slot",
            "description": "Generic metadata slot.",
            "version": "0.1.0",
            "slot_type": "module",
            "owner_scope": ["workspace:main"],
            "declared_capability_refs": ["test.echo.respond"],
        },
    )
    assert slot_response.status_code == 200
    slot_id = slot_response.json()["module_slot_id"]
    binding_response = client.post(
        "/brain/capability-bindings",
        json={
            "module_slot_id": slot_id,
            "capability_key": "test.echo.respond",
            "capability_type": "generic",
            "binding_type": "declared",
            "route_key": "test.echo.respond",
            "target_runtime": "metadata_only",
            "risk_level": "medium",
            "allowed_modes": ["dry_run"],
            "input_schema": {"type": "object", "required": ["text"]},
            "output_schema": {"type": "object", "properties": {"summary": {"type": "string"}}},
            "required_policy_actions": ["module_binding.query"],
            "required_settings": ["module_slots_enabled"],
            "required_contracts": [],
            "requires_approval": True,
            "requires_sandbox": False,
            "dry_run_supported": True,
            "controlled_supported": False,
        },
    )
    assert binding_response.status_code == 200
    binding_id = binding_response.json()["capability_binding_id"]

    profile_response = client.post(
        "/brain/conformance/profiles",
        json={"name": "Generic profile", "description": "Metadata-only profile."},
    )
    assert profile_response.status_code == 200

    seed_response = client.post("/brain/conformance/profiles/seed-defaults")
    assert seed_response.status_code == 200
    assert seed_response.json()["dry_run"] is True

    generated_response = client.post(
        f"/brain/conformance/test-vectors/generate-for-binding/{binding_id}"
    )
    assert generated_response.status_code == 200
    vector_id = generated_response.json()[0]["test_vector_id"]

    run_response = client.post(
        "/brain/conformance/run",
        json={"capability_binding_id": binding_id, "test_vector_ids": [vector_id]},
    )
    assert run_response.status_code == 200
    run = run_response.json()
    assert run["result"]["capability_executed"] is False
    assert run["result"]["source_records_mutated"] is False
    run_id = run["conformance_run_id"]

    assert client.get(f"/brain/conformance/runs/{run_id}").status_code == 200
    assert client.get("/brain/conformance/findings").status_code == 200

    readiness_response = client.post(
        "/brain/readiness/assess",
        json={"capability_binding_id": binding_id},
    )
    assert readiness_response.status_code == 200
    assert readiness_response.json()["activation_ready"] is False

    query_response = client.post(
        "/brain/conformance/query",
        json={"scope": ["workspace:main"], "capability_binding_id": binding_id},
    )
    assert query_response.status_code == 200
    assert query_response.json()["total_count"] >= 2


def test_conformance_api_rejects_executable_test_vector_payload() -> None:
    client = TestClient(create_app(kernel_container()))

    response = client.post(
        "/brain/conformance/test-vectors",
        json={
            "name": "Unsafe vector",
            "description": "Metadata-only vector.",
            "input_payload": {"command": "run"},
        },
    )

    assert response.status_code == 422
