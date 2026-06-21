"""Action proposal API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_action_proposal_api_routes_work() -> None:
    client = TestClient(create_app(kernel_container()))

    created = client.post(
        "/brain/action-proposals",
        json={
            "source_type": "user_request",
            "source_id": "source-1",
            "proposal_type": "command",
            "title": "Review generic action",
            "description": "Operator review required.",
            "action_type": "generic",
            "target_type": "noop",
            "owner_scope": ["workspace:main"],
        },
    )
    assert created.status_code == 200
    proposal_id = created.json()["action_proposal_id"]

    reviewed = client.post(
        f"/brain/action-proposals/{proposal_id}/review",
        json={
            "action_proposal_id": proposal_id,
            "decision": "approve_for_handoff",
            "reason": "reviewed",
            "approval_present": True,
        },
    )
    handoff = client.post(
        "/brain/action-proposals/handoff",
        json={
            "action_proposal_id": proposal_id,
            "handoff_type": "dry_run",
            "target_system": "noop",
        },
    )
    queried = client.post("/brain/action-proposals/query", json={"scope": ["workspace:main"]})

    assert reviewed.status_code == 200
    assert handoff.status_code == 200
    assert handoff.json()["status"] == "dry_run"
    assert queried.status_code == 200
    assert queried.json()["total_count"] == 1
