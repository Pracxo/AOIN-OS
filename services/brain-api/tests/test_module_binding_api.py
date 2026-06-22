"""Module binding API tests."""

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_module_binding_api_sequence() -> None:
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
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
            "required_policy_actions": ["module_binding.query"],
            "required_settings": ["module_slots_enabled"],
            "required_contracts": [],
            "requires_approval": True,
            "requires_sandbox": True,
            "dry_run_supported": True,
            "controlled_supported": False,
        },
    )
    assert binding_response.status_code == 200
    binding_id = binding_response.json()["capability_binding_id"]

    validation_response = client.post(
        "/brain/module-bindings/validate",
        json={
            "owner_scope": ["workspace:main"],
            "mode": "dry_run",
            "module_slot_id": slot_id,
            "capability_binding_ids": [binding_id],
        },
    )
    assert validation_response.status_code == 200
    assert validation_response.json()["result"]["activation_allowed"] is False

    mount_response = client.post(
        "/brain/module-bindings/mount-plans",
        json={"module_slot_id": slot_id, "scope": ["workspace:main"]},
    )
    assert mount_response.status_code == 200
    assert mount_response.json()["execution_allowed"] is False

    route_response = client.post(
        "/brain/module-bindings/route-previews",
        json={"capability_binding_id": binding_id, "scope": ["workspace:main"]},
    )
    assert route_response.status_code == 200
    assert route_response.json()["registration_allowed"] is False

    query_response = client.post(
        "/brain/module-bindings/query",
        json={"scope": ["workspace:main"], "query": "echo"},
    )
    assert query_response.status_code == 200
    assert query_response.json()["total_count"] >= 2
