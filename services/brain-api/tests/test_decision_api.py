from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_decision_api_endpoints_work() -> None:
    client = TestClient(create_app(kernel_container()))
    created = client.post(
        "/brain/decisions/frames",
        json={
            "title": "Choose",
            "question": "Which option?",
            "owner_scope": ["workspace:main"],
        },
    )
    assert created.status_code == 200
    frame_id = created.json()["decision_frame_id"]

    option = client.post(
        "/brain/decisions/options",
        json={
            "decision_frame_id": frame_id,
            "title": "Retrieve context",
            "description": "Retrieve more context.",
            "option_type": "retrieve_more_context",
            "risk_level": "low",
        },
    )
    assert option.status_code == 200
    option_id = option.json()["decision_option_id"]

    assert (
        client.get(
            f"/brain/decisions/frames/{frame_id}",
            params={"scope": "workspace:main"},
        ).status_code
        == 200
    )
    assert (
        client.get(
            "/brain/decisions/frames",
            params={"scope": "workspace:main"},
        ).status_code
        == 200
    )
    assert client.get(f"/brain/decisions/frames/{frame_id}/options").status_code == 200
    assert (
        client.post(
            "/brain/decisions/utility-profiles/seed-defaults",
            json={"scope": ["workspace:main"], "dry_run": True},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/brain/decisions/evaluate",
            json={"decision_frame_id": frame_id},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/brain/decisions/recommend/{frame_id}",
            json={"dry_run": True},
        ).status_code
        == 200
    )
    counterfactual = client.post(
        "/brain/decisions/counterfactuals/run",
        json={
            "decision_frame_id": frame_id,
            "decision_option_id": option_id,
            "owner_scope": ["workspace:main"],
        },
    )
    assert counterfactual.status_code == 200
    run_id = counterfactual.json()["counterfactual_run_id"]
    assert client.get(f"/brain/decisions/counterfactuals/{run_id}").status_code == 200
    record = client.post(
        "/brain/decisions/journal",
        json={
            "decision_frame_id": frame_id,
            "selected_option_id": option_id,
            "rationale": "Record only.",
        },
    )
    assert record.status_code == 200
    record_id = record.json()["decision_record_id"]
    assert (
        client.get(
            f"/brain/decisions/journal/{record_id}",
            params={"scope": "workspace:main"},
        ).status_code
        == 200
    )
    assert (
        client.get(
            "/brain/decisions/journal",
            params={"scope": "workspace:main"},
        ).status_code
        == 200
    )
