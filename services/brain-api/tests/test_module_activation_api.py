"""Module activation API tests."""

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_module_activation_api_sequence() -> None:
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
        },
    )
    assert slot_response.status_code == 200
    slot_id = slot_response.json()["module_slot_id"]

    request_response = client.post(
        "/brain/module-activation/requests",
        json={
            "module_slot_id": slot_id,
            "owner_scope": ["workspace:main"],
            "risk_level": "medium",
            "metadata": {
                "required_policy_actions": ["module_activation.query.read"],
                "required_settings": ["module_activation_requests_enabled"],
            },
        },
    )
    assert request_response.status_code == 200
    activation_request_id = request_response.json()["activation_request_id"]
    assert request_response.json()["activation_allowed"] is False

    gate_response = client.post(
        f"/brain/module-activation/requests/{activation_request_id}/gate",
        json={"scope": ["workspace:main"], "mode": "dry_run"},
    )
    assert gate_response.status_code == 200
    assert gate_response.json()["status"] == "blocked"

    blocker_response = client.get(
        "/brain/module-activation/blockers",
        params={"scope": "workspace:main", "activation_request_id": activation_request_id},
    )
    assert blocker_response.status_code == 200
    assert blocker_response.json()

    plan_response = client.post(
        f"/brain/module-activation/requests/{activation_request_id}/plans",
        json={"scope": ["workspace:main"]},
    )
    assert plan_response.status_code == 200
    assert plan_response.json()["executable"] is False

    preview_response = client.post(
        f"/brain/module-activation/requests/{activation_request_id}/runtime-registration-preview",
        json={"scope": ["workspace:main"]},
    )
    assert preview_response.status_code == 200
    assert preview_response.json()["registration_allowed"] is False

    review_response = client.post(
        "/brain/module-activation/reviews",
        params={"scope": "workspace:main"},
        json={
            "activation_request_id": activation_request_id,
            "decision": "no_action",
            "reason": "Recorded review.",
        },
    )
    assert review_response.status_code == 200

    query_response = client.post(
        "/brain/module-activation/query",
        json={"scope": ["workspace:main"], "activation_request_id": activation_request_id},
    )
    assert query_response.status_code == 200
    assert query_response.json()["total_count"] >= 4
