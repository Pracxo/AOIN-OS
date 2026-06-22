from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_run_supervision_api_routes_work() -> None:
    client = TestClient(create_app(kernel_container()))

    created = client.post(
        "/brain/run-supervision/runs",
        json={
            "source_type": "generic",
            "source_id": "source-api",
            "target_system": "noop",
            "run_type": "generic",
            "owner_scope": ["workspace:main"],
            "title": "Supervise noop",
            "description": "Observe a noop run.",
        },
    )
    assert created.status_code == 200
    run_id = created.json()["run_supervision_id"]

    assert (
        client.get(
            f"/brain/run-supervision/runs/{run_id}", params={"scope": "workspace:main"}
        ).status_code
        == 200
    )
    assert (
        client.get("/brain/run-supervision/runs", params={"scope": "workspace:main"}).status_code
        == 200
    )
    assert (
        client.post(
            f"/brain/run-supervision/runs/{run_id}/sample", json={"scope": ["workspace:main"]}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/brain/run-supervision/sample-many", json={"scope": ["workspace:main"]}
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/brain/run-supervision/runs/{run_id}/archive", json={"reason": "done"}
        ).status_code
        == 200
    )

    control = client.post(
        "/brain/run-supervision/control-requests",
        json={"run_supervision_id": run_id, "control_type": "request_status", "reason": "check"},
    )
    assert control.status_code == 200
    control_id = control.json()["run_control_request_id"]
    assert client.get("/brain/run-supervision/control-requests").status_code == 200
    assert (
        client.post(
            f"/brain/run-supervision/control-requests/{control_id}/handoff", json={}
        ).status_code
        == 200
    )

    policy = client.post(
        "/brain/run-supervision/timeout-policies",
        json={
            "timeout_policy_id": "policy-api",
            "name": "api-policy",
            "description": "Policy",
            "status": "active",
            "target_system": "noop",
            "run_type": "generic",
            "timeout_seconds": 10,
            "stall_after_seconds": 5,
            "max_status_age_seconds": 5,
            "severity": "medium",
            "action_on_timeout": "report_only",
            "owner_scope": ["workspace:main"],
        },
    )
    assert policy.status_code == 200
    assert (
        client.get(
            "/brain/run-supervision/timeout-policies", params={"scope": "workspace:main"}
        ).status_code
        == 200
    )

    plan = client.post(
        f"/brain/run-supervision/runs/{run_id}/propose-compensation",
        json={"trigger_reason": "manual_review"},
    )
    assert plan.status_code == 200
    plan_id = plan.json()["compensation_plan_id"]
    assert (
        client.get(
            f"/brain/run-supervision/compensation-plans/{plan_id}",
            params={"scope": "workspace:main"},
        ).status_code
        == 200
    )
    assert (
        client.get(
            "/brain/run-supervision/compensation-plans", params={"scope": "workspace:main"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/brain/run-supervision/compensation-plans/{plan_id}/approve",
            json={"reason": "approved"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/brain/run-supervision/compensation-plans/{plan_id}/convert-to-action-proposals",
            json={"reason": "convert", "approval_present": True},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/brain/run-supervision/reports", json={"owner_scope": ["workspace:main"]}
        ).status_code
        == 200
    )
