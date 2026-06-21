from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_run_supervision_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.run_supervision.create_run({"owner_scope": ["workspace:main"]})
    client.run_supervision.get_run("run-1", ["workspace:main"])
    client.run_supervision.list_runs(["workspace:main"])
    client.run_supervision.sample("run-1", ["workspace:main"])
    client.run_supervision.sample_many(["workspace:main"])
    client.run_supervision.archive("run-1", "done")
    client.run_supervision.create_control_request({"run_supervision_id": "run-1"})
    client.run_supervision.list_control_requests(run_supervision_id="run-1")
    client.run_supervision.handoff_control("control-1")
    client.run_supervision.create_timeout_policy({"timeout_policy_id": "policy-1"})
    client.run_supervision.list_timeout_policies(["workspace:main"])
    client.run_supervision.create_compensation_plan({"source_id": "source-1"})
    client.run_supervision.propose_compensation("run-1", "failed")
    client.run_supervision.get_compensation_plan("plan-1", ["workspace:main"])
    client.run_supervision.list_compensation_plans(["workspace:main"])
    client.run_supervision.approve_compensation_plan("plan-1", "approved")
    client.run_supervision.convert_compensation_to_action_proposals("plan-1", "convert")
    client.run_supervision.create_report({"owner_scope": ["workspace:main"]})

    assert seen == [
        ("POST", "/brain/run-supervision/runs"),
        ("GET", "/brain/run-supervision/runs/run-1"),
        ("GET", "/brain/run-supervision/runs"),
        ("POST", "/brain/run-supervision/runs/run-1/sample"),
        ("POST", "/brain/run-supervision/sample-many"),
        ("POST", "/brain/run-supervision/runs/run-1/archive"),
        ("POST", "/brain/run-supervision/control-requests"),
        ("GET", "/brain/run-supervision/control-requests"),
        ("POST", "/brain/run-supervision/control-requests/control-1/handoff"),
        ("POST", "/brain/run-supervision/timeout-policies"),
        ("GET", "/brain/run-supervision/timeout-policies"),
        ("POST", "/brain/run-supervision/compensation-plans"),
        ("POST", "/brain/run-supervision/runs/run-1/propose-compensation"),
        ("GET", "/brain/run-supervision/compensation-plans/plan-1"),
        ("GET", "/brain/run-supervision/compensation-plans"),
        ("POST", "/brain/run-supervision/compensation-plans/plan-1/approve"),
        ("POST", "/brain/run-supervision/compensation-plans/plan-1/convert-to-action-proposals"),
        ("POST", "/brain/run-supervision/reports"),
    ]


def test_run_supervision_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.run_supervision as resource

    assert "aion_brain" not in resource.__dict__
