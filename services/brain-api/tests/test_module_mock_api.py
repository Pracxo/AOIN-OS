"""Module mock runtime API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_module_mock_api_endpoints_work() -> None:
    client = TestClient(create_app(kernel_container()))
    slot_id, binding_id = _create_slot_and_binding(client)

    profile = client.post(
        "/brain/module-mock/profiles",
        json={
            "profile_key": "generic.mock",
            "name": "Generic Mock",
            "description": "Generic mock profile.",
            "owner_scope": ["workspace:main"],
        },
    )
    seed = client.post(
        "/brain/module-mock/profiles/seed-defaults",
        json={"scope": ["workspace:main"], "dry_run": True},
    )
    listed_profiles = client.get(
        "/brain/module-mock/profiles",
        params={"scope": "workspace:main"},
    )
    fetched_profile = client.get(
        f"/brain/module-mock/profiles/{profile.json()['mock_profile_id']}",
        params={"scope": "workspace:main"},
    )
    run = client.post(
        "/brain/module-mock/invoke",
        json={
            "module_slot_id": slot_id,
            "capability_binding_id": binding_id,
            "capability_key": "generic.knowledge.answer",
            "invocation_type": "mock_answer",
            "mode": "dry_run",
            "owner_scope": ["workspace:main"],
            "input_payload": {"query": "generic test query"},
            "expected_output_shape": {"type": "object", "synthetic": True},
        },
    )
    run_body = run.json()
    output_id = run_body["output"]["module_mock_output_id"]
    listed_runs = client.get("/brain/module-mock/runs", params={"scope": "workspace:main"})
    fetched_run = client.get(
        f"/brain/module-mock/runs/{run_body['module_mock_run_id']}",
        params={"scope": "workspace:main"},
    )
    listed_outputs = client.get(
        "/brain/module-mock/outputs",
        params={"scope": "workspace:main"},
    )
    fetched_output = client.get(
        f"/brain/module-mock/outputs/{output_id}",
        params={"scope": "workspace:main"},
    )
    findings = client.get("/brain/module-mock/findings", params={"scope": "workspace:main"})
    query = client.post("/brain/module-mock/query", json={"scope": ["workspace:main"]})

    assert [
        item.status_code
        for item in [
            profile,
            seed,
            listed_profiles,
            fetched_profile,
            run,
            listed_runs,
            fetched_run,
            listed_outputs,
            fetched_output,
            findings,
            query,
        ]
    ] == [200] * 11
    assert seed.json()["dry_run"] is True
    assert run_body["mode"] == "dry_run"
    assert run_body["activation_allowed"] is False
    assert run_body["execution_allowed"] is False
    assert fetched_output.json()["redacted_output_payload"]["synthetic"] is True
    assert listed_outputs.json()
    assert query.json()["metadata"]["code_loaded"] is False


def test_module_mock_runtime_compatibility_prefix_still_works() -> None:
    client = TestClient(create_app(kernel_container()))

    response = client.post(
        "/brain/module-mock-runtime/profiles/seed",
        json={"scope": ["workspace:main"], "dry_run": True},
    )

    assert response.status_code == 200
    assert response.json()["profile_count"] == 7


def _create_slot_and_binding(client: TestClient) -> tuple[str, str]:
    slot_response = client.post(
        "/brain/module-slots",
        json={
            "slot_key": "generic.knowledge",
            "name": "Generic Knowledge Slot",
            "description": "Generic metadata slot.",
            "version": "0.1.0",
            "slot_type": "module",
            "owner_scope": ["workspace:main"],
            "declared_capability_refs": ["generic.knowledge.answer"],
        },
    )
    assert slot_response.status_code == 200
    slot_id = slot_response.json()["module_slot_id"]
    binding_response = client.post(
        "/brain/capability-bindings",
        json={
            "module_slot_id": slot_id,
            "capability_key": "generic.knowledge.answer",
            "capability_type": "generic",
            "binding_type": "declared",
            "route_key": "generic.knowledge.answer",
            "target_runtime": "metadata_only",
            "risk_level": "medium",
            "allowed_modes": ["dry_run"],
            "input_schema": {"type": "object", "required": ["query"]},
            "output_schema": {"type": "object", "synthetic": True},
            "required_policy_actions": ["module_mock.invoke"],
            "required_settings": ["module_mock_runtime_enabled"],
            "required_contracts": [],
            "requires_approval": True,
            "requires_sandbox": True,
            "dry_run_supported": True,
            "controlled_supported": False,
        },
    )
    assert binding_response.status_code == 200
    return slot_id, str(binding_response.json()["capability_binding_id"])
