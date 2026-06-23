from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_operator_action_api_endpoints_work() -> None:
    client = TestClient(create_app(kernel_container()))

    created = client.post(
        "/brain/operator-actions/requests",
        json={
            "action_key": "operator.review",
            "action_type": "generic",
            "target_type": "generic",
            "owner_scope": ["workspace:main"],
            "request_payload": {"summary": "review local record"},
        },
    )
    assert created.status_code == 200
    payload = created.json()
    request_id = payload["operator_action_request_id"]
    assert payload["mode"] == "dry_run"
    assert payload["execution_allowed"] is False

    fetched = client.get(
        f"/brain/operator-actions/requests/{request_id}",
        params={"scope": ["workspace:main"]},
    )
    listed = client.get(
        "/brain/operator-actions/requests",
        params={"scope": ["workspace:main"]},
    )
    previewed = client.post(
        f"/brain/operator-actions/requests/{request_id}/preview",
        json={"scope": ["workspace:main"]},
    )
    blockers = client.get(
        "/brain/operator-actions/blockers",
        params={"scope": ["workspace:main"], "operator_action_request_id": request_id},
    )
    reviewed = client.post(
        f"/brain/operator-actions/requests/{request_id}/review",
        json={
            "operator_action_request_id": request_id,
            "decision": "approve_preview_only",
            "reason": "reviewed",
            "approval_present": True,
        },
    )
    reviews = client.get(
        "/brain/operator-actions/reviews",
        params={"scope": ["workspace:main"], "operator_action_request_id": request_id},
    )
    queried = client.post(
        "/brain/operator-actions/query",
        json={"scope": ["workspace:main"], "limit": 50},
    )

    assert fetched.status_code == 200
    assert listed.status_code == 200
    assert previewed.status_code == 200
    assert previewed.json()["would_execute"] is False
    assert blockers.status_code == 200
    assert blockers.json()
    assert reviewed.status_code == 200
    assert reviewed.json()["execution_allowed"] is False
    assert reviews.status_code == 200
    assert queried.status_code == 200
    assert queried.json()["total_count"] >= 1


def test_operator_action_blocker_dismiss_api_does_not_enable_execution() -> None:
    client = TestClient(create_app(kernel_container()))
    created = client.post(
        "/brain/operator-actions/requests",
        json={
            "action_key": "operator.review",
            "owner_scope": ["workspace:main"],
            "request_payload": {"summary": "review local record"},
            "create_preview": False,
        },
    )
    blocker_id = created.json()["blocker_refs"][0]

    dismissed = client.post(
        f"/brain/operator-actions/blockers/{blocker_id}/dismiss",
        json={"reason": "reviewed"},
    )

    assert dismissed.status_code == 200
    assert dismissed.json()["status"] == "dismissed"
    assert dismissed.json()["metadata"]["execution_allowed"] is False
